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

import argparse
import logging

from .static import StaticGenerator

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(
        description=('Generate a collection of static HTML pages from a '
                     'collection of markdown documents'))
    parser.add_argument('-c', '--config', default='config.ini', help="An "
                        "alternate configuration file (other than "
                        "'config.ini')")
    parser.add_argument('--bootstrap', dest="bootstrap", action="store_true",
                        help="Initial setup step to create configuration file "
                        "and necessary templates")
    args = parser.parse_args()
    if args.bootstrap:
        bootstrap()
    else:
        s = StaticGenerator(config_file=args.config)
        s.configure()
        s.process_posts()
        s.write_generated_files()
        s.copy_media()

def bootstrap():
    import os

    config = 'config.ini', """
[STATIC]
domain =
name =
author =
output directory = build
posts directory = posts
media directory = media
templates directory = templates
date format = %Y-%m-%d
feed link = feed.atom
""".lstrip()

    archive = 'templates/archive.html', """
{% extends "base.html" %}
{% block content %}
{% for post in all_posts %}
<a href="{{ post.path }}">{{ post.title }}</a>
{% endfor %}
{% endblock %}
""".lstrip()

    base = 'templates/base.html', """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <base href='/'></base>
  </head>
  <body>
    {% block content %}
    {% endblock %}
  </body>
</html>
""".lstrip()

    post = 'templates/post.html', """
{% extends "base.html" %}
{% block content %}
{{ post.title }}
{{ post.body_markup }}
{% endblock %}
""".lstrip()

    index = 'templates/index.html', """
{% extends "base.html" %}
{% block content %}
{% for post in front_posts %}
  <a href={{ post.path }}>{{ post.title }}</a>
  {{ post.leader }}
{% endfor %}
{% endblock %}
""".lstrip()

    for directory in ('templates', 'posts', 'build'):
        try:
            os.makedirs(directory)
        except Exception:
            logger.warning(f'{directory} directory already exists')

    for each_file, template in (config, base, index, archive, post):
        try:
            with open(each_file, 'x') as f:
                f.write(template)
        except FileExistsError:
            logger.warning(f'{each_file} already exists')
