#!/usr/bin/env python3

from datetime import datetime as dt
import urllib
import json
import sys
import os
import re

from mistune import Markdown
from jinja2 import Environment, PackageLoader

# TODO: some functions/no use of self happening here
class StaticGenerator():
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self.read_config_file()
        self._separator = re.compile(r'^===$', re.MULTILINE)
        self.markdown = Markdown()
        self.all_posts = []

    def read_config_file(self):
        with open(self.config_file) as f:
            config = json.load(f)
        return config

    def read_file(self, filename):
        with open(filename) as f:
            return f.read()

    def write_output_file(self, contents, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, mode='w', encoding='utf8') as outfile:
            outfile.write(contents)

    def templatize_post(self, post,
                        template_name='post.html', template_dir='templates'):
        env = Environment(loader=PackageLoader('static', template_dir))
        template = env.get_template(template_name)
        return template.render(post=post)

    def collect_posts(self, from_dir):
        for root, _, files in os.walk(from_dir):
            for _file in files:
                if _file.endswith('.md'):
                    yield (root, _file)

    def split_post(self, content):
        _split_contents = self._separator.split(content, maxsplit=1)
        if len(_split_contents) < 2:
            raise TypeError("Failed to parse Post header")
        return _split_contents

    def parse_date(self, date_string, date_format='%Y-%m-%d'):
        try:
            return dt.strptime(date_string, date_format)
        except ValueError as err:
            raise TypeError("Failed to parse date from: {} - expected {}"
                            .format(date_string, date_format))

    def parse_post_parts(self, header_string, body):
        _post = dict()
        _header, _post['_body'] = header_string, body
        kv_string = _header.lower().strip().split('\n')
        kv_pairs = (pair.split(':', maxsplit=1) for pair in kv_string)
        _post.update({ key: value.strip() for key, value in kv_pairs })
        if 'date' in _post:
            _post['date'] = self.parse_date(_post['date'])
        return _post

    def sort_posts_by_date(self, posts):
        """Relies on the `posts` input being a list of dictionaries with a header-date
        field, taken care of by `create_posts`"""
        return sorted(posts, key=lambda post: post['date'], reverse=True)

    def create_posts(self):
        posts_dir = self.config['posts_dir']
        output_dir = self.config['output_dir']

        for directory, filename in self.collect_posts(posts_dir):
            post_file = os.path.join(directory, filename)
            raw_text = self.read_file(post_file)
            header_string, body = self.split_post(raw_text)
            post = self.parse_post_parts(header_string, body)

            post['_body'] = self.markdown(post['_body'])
            templated_html = self.templatize_post(post)
            _outdir = re.sub(posts_dir, output_dir, directory)
            _outfile = re.sub('.md', '.html', filename)

            out_path = os.path.join(_outdir, _outfile)
            self.write_output_file(templated_html, out_path)

            if 'date' in post:
                self.all_posts.append(post)

        self.all_posts = self.sort_posts_by_date(self.all_posts)

    # TODO: this isn't really written yet. This is more like a sketch. Atom
    # feed requires more information. How are IDs going to be handled?
    def create_feed(self, post_limit=10):
        env = Environment(loader=PackageLoader('static', 'templates'))
        env.filters['slugify'] = slugify
        template = env.get_template('atom_feed.template')
        recent_posts = self.all_posts[:post_limit]
        return template.render(recent_posts=recent_posts, config=self.config)

    def create_archive(self):
        raise NotImplementedError

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
