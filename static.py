#!/usr/bin/env python3

# Copyright 2017 Nolan Prescott
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from datetime import datetime, timezone
import argparse
import urllib
import shutil
import json
import sys
import os
import re

from mistune import Markdown
from jinja2 import Environment, FileSystemLoader

from feed import feed, render_feed


class StaticGenerator():
    def __init__(self, config_file="config.json", save=False):
        self.config_file = config_file
        self.save = save
        self.config = self.read_config()
        self._separator = re.compile(r'^===$', re.MULTILINE)
        self.markdown = Markdown()
        self._env = Environment(
            loader=FileSystemLoader(self.config['templates_dir'])
        )
        self._post_template = self._env.get_template('post.html')
        self.all_posts = self.load_rendered(self.config['prerender_file'])

    def dump_rendered(self, json_file):
        _posts = [{ 'filename': post['filename'],
                    'title':    post['title'],
                    'date':     post['date'].strftime(self.config['date_format']),
                    'path':     post['path'],
                    'body':     post['body']}
                  for post in self.all_posts]
        with open(json_file, 'w') as f:
            json.dump(_posts, f)

    def load_rendered(self, json_file):
        try:
            with open(json_file) as f:
                save_file = json.load(f)
                for entry in save_file:
                    _date = datetime.strptime(entry['date'],
                                              self.config['date_format'])
                    entry['date'] = _date.replace(tzinfo=timezone.utc)
                return save_file

        except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
            return []

    def is_prerendered(self, filename):
        return any(filename in dictionary.values()
                   for dictionary in self.all_posts)

    def read_config(self):
        raw_config = to_string(self.config_file)
        return json.loads(raw_config)

    def templatize_post(self, post_obj):
        return self._post_template.render(post=post_obj)

    def collect_posts(self, from_dir):
        for root, _, files in os.walk(from_dir):
            for _file in files:
                if _file.endswith('.md'):
                    yield (root, _file)

    def find_media_dir_paths(self, dirname):
        for root, directories, files in os.walk(dirname):
            for directory in directories:
                if directory == self.config['media_dir']:
                    yield os.path.join(root, directory)

    def copy_media(self):
        input_dir = self.config['posts_dir']
        out_dir = self.config['output_dir']
        media_dirs = self.find_media_dir_paths(input_dir)
        for each_dir in media_dirs:
            relative_dest_dir = re.sub(input_dir, '', each_dir, count=1)
            out_path = os.path.join(out_dir, relative_dest_dir)
            os.makedirs(out_path, exist_ok=True)
            for filename in os.listdir(each_dir):
                shutil.copy(os.path.join(each_dir, filename), out_path)

    def split_post(self, content):
        _split_contents = self._separator.split(content, maxsplit=1)
        if len(_split_contents) < 2:
            raise TypeError("Failed to parse post from: {}..."
                            .format(content[:50]))
        return _split_contents

    def parse_date(self, date_string):
        """
        returns: datetime with timezone in UTC
        """
        try:
            _date = datetime.strptime(date_string, self.config['date_format'])
            return _date.replace(tzinfo=timezone.utc)
        except ValueError as err:
            raise TypeError("Failed to parse date from: {} - expected {}"
                            .format(date_string, self.config['date_format']))

    def parse_header(self, header_string):
        kv_list_pairs = header_string.strip().split('\n')
        kv_pairs = (pair.split(':', maxsplit=1) for pair in kv_list_pairs)
        try:
            return { key.lower(): value.strip() for key, value in kv_pairs }
        except ValueError as err:
            raise TypeError("Improperly formatted header: {}"
                            .format(kv_list_pairs))

    def parse_post_parts(self, header_string, body):
        post = self.parse_header(header_string)
        post['body'] = body
        if 'date' in post:
            post['date'] = self.parse_date(post['date'])
        return post

    def sort_posts_by_date(self, posts):
        """
        Relies on the posts input being a list of dictionaries with a date field
        """
        return sorted(posts, key=lambda post: post['date'], reverse=True)

    # TODO: needs tests
    def create_posts(self):
        posts_dir = self.config['posts_dir']
        output_dir = self.config['output_dir']

        for directory, filename in self.collect_posts(posts_dir):
            if not self.is_prerendered(filename):
                post_file = os.path.join(directory, filename)
                raw_text = to_string(post_file)
                header_string, body = self.split_post(raw_text)
                post = self.parse_post_parts(header_string, body)
                post['body'] = self.markdown(post['body'])
                templated_html = self.templatize_post(post)
                relative_dir = re.sub(posts_dir, '', directory, count=1)

                # in case I want to directly specify the generated URI/filename
                # (as in the case of an index) without having to title it
                # "index"
                if 'altname' in post:
                    _filename = post['altname']
                else:
                    _filename = '{}.html'.format(slugify(post['title']))

                post['path'] = os.path.join(relative_dir, _filename)
                full_path = os.path.join(output_dir, relative_dir, _filename)
                write_to_file(templated_html, full_path)

                if 'date' in post:
                    self.all_posts.append({'filename': filename,
                                           'title':    post['title'],
                                           'date':     post['date'],
                                           'path':     post['path'],
                                           'body':     post['body']})

        self.all_posts = self.sort_posts_by_date(self.all_posts)

        if self.save:
            self.dump_rendered(self.config['prerender_file'])

    def write_archive(self):
        if self.all_posts:
            archive = self.render_archive()
            archive_path = os.path.join(self.config['output_dir'], 'archive.html')
            write_to_file(archive, archive_path)
        else:
            raise ValueError("StaticGenerator has no posts to create archive")

    def render_archive(self, template_name='archive.html'):
        env = Environment(loader=FileSystemLoader(self.config['templates_dir']))
        template = env.get_template(template_name)
        return template.render(all_posts=self.all_posts)

    # relatively linked content (images in <year>/static/) don't work
    def _feed_string(self, post_limit=10):
        recent_posts = self.all_posts[:post_limit]
        return render_feed(feed(recent_posts, **self.config))

    def write_feed(self):
        # feed is utf-8 bytes
        feed = self._feed_string()
        output_path = os.path.join(self.config['output_dir'], 'feed.atom')
        with open(output_path, 'wb') as f:
            f.write(feed)

# small utility functions
def to_string(filename):
    with open(filename) as f:
        return f.read()

def write_to_file(contents, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, mode='w', encoding='utf8') as outfile:
        outfile.write(contents)

def slugify(text):
    '''Build hyphenated post slugs from "unsafe" text. RFC3986 requires percent
    encoding for UCS/unicode points.

    Examples:
    >>> slugify("Wow, 2015 has \"Come and Gone\" already! It's amazing.")
    'wow-2015-has-come-and-gone-already-its-amazing'

    >>> slugify("λ is a lambda")
    '%CE%BB-is-a-lambda'

    '''
    QUOTES = re.compile(r'[\"\']')
    MULTIPLE_DASH = re.compile(r'-+')
    NOT_CHAR = re.compile(r'[\W]')

    _string = QUOTES.sub('', text)
    _string = _string.lower()
    _string = NOT_CHAR.sub('-', _string)
    _string = MULTIPLE_DASH.sub('-', _string)
    _string = urllib.parse.quote(_string, safe='-')
    output_string = _string.strip('-')

    return output_string

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generate a collection of static HTML pages'
    )
    parser.add_argument('-c', '--config', default='config.json')
    parser.add_argument('--save', dest='save', action='store_true')

    args = parser.parse_args()
    s = StaticGenerator(config_file=args.config, save=args.save)

    s.create_posts()
    s.write_archive()
    s.write_feed()
    s.copy_media()
