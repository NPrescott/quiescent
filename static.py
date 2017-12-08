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

import configparser
import argparse
import logging
import shutil
import json
import os
import re

from jinja2 import Environment, FileSystemLoader

from post import Post
from feed import feed, render_feed

logger = logging.getLogger(__name__)


class StaticGenerator():
    def __init__(self, config_file=None):
        self.config_file = config_file
        self.config = None
        self.all_posts = []
        self.template_environment = None
        self.post_template = None

    def configure(self):
        self.config = configparser.ConfigParser(interpolation=None)
        self.config.read(self.config_file)
        self.config = self.config['STATIC']
        self.template_environment = Environment(
            loader=FileSystemLoader(self.config['templates directory'])
        )
        self.post_template = self.template_environment.get_template('post.html')

    @staticmethod
    def collect_posts(from_dir):
        '''
        Walk the directory containing posts and return any with a `.md` suffix
        '''
        for root, _, files in os.walk(from_dir):
            for _file in files:
                if _file.endswith('.md'):
                    yield (root, _file)

    def find_media_directories(self, dirname):
        for root, directories, files in os.walk(dirname):
            for directory in directories:
                if directory == self.config['media directory']:
                    yield os.path.join(root, directory)

    def copy_media(self):
        '''
        There may be some potential for optimization here, everything is copied
        every time (which has the nice effect of grabbing updated files with
        the same name). Thus far the time spent has been low.
        '''
        input_dir = self.config['posts directory']
        out_dir = self.config['output directory']
        media_dirs = self.find_media_directories(input_dir)
        for each_dir in media_dirs:
            relative_dest_dir = os.path.relpath(each_dir, input_dir)
            out_path = os.path.join(out_dir, relative_dest_dir)
            os.makedirs(out_path, exist_ok=True)
            for filename in os.listdir(each_dir):
                shutil.copy(os.path.join(each_dir, filename), out_path)

    @staticmethod
    def sort_posts_by_date(posts):
        return sorted(posts, key=lambda post: post.date, reverse=True)

    def process_posts(self):
        for directory, filename in self.collect_posts(self.config['posts directory']):

            post = Post(indir=self.config['posts directory'],
                        outdir=self.config['output directory'],
                        directory=directory,
                        filename=filename,
                        template=self.post_template)
            try:
                post.create_post()
                self.all_posts.append(post)
            except ValueError as e:
                logger.warning(f'Failed to create post: {post}\n{e}')
        self.all_posts = self.sort_posts_by_date(self.all_posts)

    def write_archive(self):
        if self.all_posts:
            archive = self.render_archive()
            archive_path = os.path.join(self.config['output directory'], 'archive.html')
            write_to_file(archive, archive_path)
        else:
            raise ValueError("StaticGenerator has no posts to create archive")

    def write_index(self):
        if self.all_posts:
            index = self.render_index()
            index_path = os.path.join(self.config['output directory'], 'index.html')
            write_to_file(index, index_path)
        else:
            raise ValueError("StaticGenerator has no posts to create index")

    def render_page(self, template_name, **kwargs):
        template = self.template_environment.get_template(template_name)
        return template.render(**kwargs)

    def write_generated_files(self):
        index_path = os.path.join(self.config['output directory'], 'index.html')
        index = s.render_page('index.html', front_posts=self.all_posts[:10])
        with open(index_path, 'w') as f:
            f.write(index)

        archive_path = os.path.join(self.config['output directory'], 'archive.html')
        archive = s.render_page('archive.html', all_posts=self.all_posts)
        with open(archive_path, 'w') as f:
            f.write(archive)

        self.write_feed()

    def _feed_string(self, post_limit=10):
        recent_posts = self.all_posts[:post_limit]
        return render_feed(feed(recent_posts, **self.config))

    def write_feed(self):
        # feed is utf-8 bytes
        feed = self._feed_string()
        output_path = os.path.join(self.config['output directory'],
                                  self.config['feed link'])
        with open(output_path, 'wb') as f:
            f.write(feed)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=('Generate a collection of static HTML pages from a '
                     'collection of markdown documents'))
    parser.add_argument('-c', '--config', default='config.ini')

    args = parser.parse_args()
    s = StaticGenerator(config_file=args.config)
    s.configure()
    s.process_posts()
    s.write_generated_files()
    s.copy_media()
