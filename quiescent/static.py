#!/usr/bin/env python3

# Copyright 2018 Nolan Prescott
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
import configparser
import argparse
import logging
import shutil
import json
import sys
import os
import re

from .post import Post
from .feed import feed
from .templite import Templite

logger = logging.getLogger(__name__)


class StaticGenerator:
    def __init__(self, config_file=None):
        self.config_file = config_file
        self.config = None
        self.all_posts = []
        self.index_template = 'index.html'
        self.archive_template = 'archive.html'
        self.post_template = 'post.html'

    def configure(self):
        try:
            config = configparser.ConfigParser(interpolation=None)
            config.read(self.config_file)
            self.config = config['STATIC']
            self.output_dir = self.config['output directory']
            self.posts_dir = self.config['posts directory']
            self.media_dir = self.config['media directory']
            self.author = self.config['author']
            self.domain = self.config['domain']
            self.feed_name = self.config['name']
            self.feed_link = self.config['feed link']
            self.template_dir = self.config['templates directory']
        except Exception as e:
            logger.error("An error occurred in initial configuration, do "
                         "you have the necessary configuration file and "
                         "templates?\n\tTry using the --boostrap command")
            sys.exit(1)

    def collect_posts(self, from_dir):
        '''
        Walk the directory containing posts and return any with a `.md` suffix as a
        tuple of (directory, filename)
        '''
        post_files = []
        for root, _, files in os.walk(from_dir):
            for _file in files:
                if _file.endswith('.md'):
                    post_files.append((root, _file))
        return post_files

    def find_media_directories(self, directory, media_directory):
        directory_paths = []
        for root, directories, _ in os.walk(directory):
            for dir in directories:
                if dir == media_directory:
                    directory_paths.append(os.path.join(root, dir))
        return directory_paths

    def copy_media(self):
        # There may be some potential for optimization here, everything is
        # copied every time, which has the nice effect of grabbing updated
        # files with the same name
        media_dirs = self.find_media_directories(self.posts_dir, self.media_dir)
        for each_dir in media_dirs:
            relative_dest_dir = os.path.relpath(each_dir, self.posts_dir)
            out_path = os.path.join(self.output_dir, relative_dest_dir)
            os.makedirs(out_path, exist_ok=True)
            for filename in os.listdir(each_dir):
                shutil.copy(os.path.join(each_dir, filename), out_path)

    def process_posts(self):
        for directory, filename in self.collect_posts(self.posts_dir):
            file_path = os.path.join(directory, filename)
            with open(file_path) as f:
                text = f.read()
            try:
                relative_dir = os.path.relpath(directory, self.posts_dir)
                post = Post(relative_dir=relative_dir).parse(text)
                self.all_posts.append(post)
            except ValueError as e:
                logger.warning(f'Failed to create post: {post}\n\t{e}')
        self.all_posts = sorted(self.all_posts)

    def render_page(self, template_name, **kwargs):
        template_file = os.path.join(self.template_dir, template_name)
        with open(template_file) as f:
            template_text = f.read()
        template = Templite(template_text)
        return template.render(kwargs)

    def write_generated_files(self):
        for post in self.all_posts:
            post_page = self.render_page(self.post_template, post=post)
            output_tree = os.path.join(self.output_dir, post.relative_dir)
            # reconstitute the input tree in the output directory
            os.makedirs(output_tree, exist_ok=True)
            output_path = os.path.join(self.output_dir, post.path)
            with open(output_path, 'w') as f:
                f.write(post_page)

        index_path = os.path.join(self.output_dir, self.index_template)
        index = self.render_page(self.index_template,
                                 front_posts=self.all_posts[:10])
        with open(index_path, 'w') as f:
            f.write(index)

        archive_path = os.path.join(self.output_dir, self.archive_template)
        archive = self.render_page(self.archive_template,
                                   all_posts=self.all_posts)
        with open(archive_path, 'w') as f:
            f.write(archive)

        self.write_feed()

    def write_feed(self, post_limit=10):
        recent_posts = self.all_posts[:post_limit]
        feed_string = feed(recent_posts,
                           date=datetime.now(timezone.utc),
                           name=self.feed_name,
                           domain=self.domain,
                           feed_link=self.feed_link,
                           feed_author=self.author)
        output_path = os.path.join(self.output_dir, self.feed_link)
        with open(output_path, 'wb') as f:
            f.write(feed_string.encode())
