#!/usr/bin/env python3

from datetime import datetime as dt
import urllib
import json
import sys
import os
import re

from mistune import Markdown
from jinja2 import Environment, PackageLoader


class StaticGenerator():
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self.read_config()
        self._separator = re.compile(r'^===$', re.MULTILINE)
        self.markdown = Markdown()
        self.all_posts = []

    def read_config(self):
        raw_config = read_file(self.config_file)
        return json.loads(raw_config)

    def templatize_post(self, post_obj, template_name='post.html'):
        env = Environment(loader=PackageLoader('static', self.config['templates_dir']))
        template = env.get_template(template_name)
        return template.render(post=post_obj)

    def collect_posts(self, from_dir):
        for root, _, files in os.walk(from_dir):
            for _file in files:
                if _file.endswith('.md'):
                    yield (root, _file)

    def split_post(self, content):
        _split_contents = self._separator.split(content, maxsplit=1)
        if len(_split_contents) < 2:
            raise TypeError("Failed to parse post from: {}..."
                            .format(content[:50]))
        return _split_contents

    def parse_date(self, date_string):
        try:
            return dt.strptime(date_string, self.config['date_format'])
        except ValueError as err:
            raise TypeError("Failed to parse date from: {} - expected {}"
                            .format(date_string, self.config['date_format']))

    def parse_header(self, header_string):
        kv_list_pairs = header_string.strip().split('\n')
        kv_pairs = (pair.split(':', maxsplit=1) for pair in kv_list_pairs)
        try:
            return { key.lower(): value.strip() for key, value in kv_pairs }
        except ValueError as err:
            raise TypeError("Improperly formatted header: {}".format(kv_list_pairs))

    def parse_post_parts(self, header_string, body):
        post = {}
        post['body'] = body
        header = self.parse_header(header_string)
        post.update(header)
        if 'date' in post:
            post['date'] = self.parse_date(post['date'])
        return post

    def sort_posts_by_date(self, posts):
        """Relies on the posts input being a list of dictionaries with a date field"""
        return sorted(posts, key=lambda post: post['date'], reverse=True)

    # TODO: needs tests
    def create_posts(self):
        posts_dir = self.config['posts_dir']
        output_dir = self.config['output_dir']

        for directory, filename in self.collect_posts(posts_dir):
            post_file = os.path.join(directory, filename)
            raw_text = read_file(post_file)
            header_string, body = self.split_post(raw_text)
            post = self.parse_post_parts(header_string, body)
            post['body'] = self.markdown(post['body'])
            templated_html = self.templatize_post(post)
            relative_dir = re.sub(posts_dir, '', directory, count=1)

            # in case I want to directly specify the generated URI/filename (as
            # in the case of an index) without having to title it "index"
            if 'altname' in post:
                _filename = post['altname']
            else:
                _filename = '{}.html'.format(slugify(post['title']))                

            post['path'] = os.path.join(relative_dir, _filename)
            full_path = os.path.join(output_dir, relative_dir, _filename)
            write_output_file(templated_html, full_path)

            if 'date' in post:
                self.all_posts.append(post)

        self.all_posts = self.sort_posts_by_date(self.all_posts)

    def write_archive(self):
        if self.all_posts:
            archive = self.create_archive()
            archive_path = os.path.join(self.config['output_dir'], 'archive.html')
            write_output_file(archive, archive_path)
        else:
            raise ValueError("StaticGenerator has no posts to create archive")
    
    def create_archive(self, template_name='archive.html'):
        env = Environment(loader=PackageLoader('static', self.config['templates_dir']))
        template = env.get_template(template_name)
        return template.render(all_posts=self.all_posts)

    # TODO: this isn't really written yet. This is more like a sketch. Atom
    # feed requires more information. How are IDs going to be handled?
    def create_feed(self, post_limit=10):
        env = Environment(loader=PackageLoader('static', 'templates'))
        template = env.get_template('atom_feed.template')
        recent_posts = self.all_posts[:post_limit]
        return template.render(recent_posts=recent_posts, config=self.config)

# small utility functions
def read_file(filename):
    with open(filename) as f:
        return f.read()

def write_output_file(contents, path):
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
    s = StaticGenerator()
    s.create_posts()
