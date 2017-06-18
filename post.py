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
import logging
import urllib
import os
import re

from mistune import Markdown


logger = logging.getLogger(__name__)


class Post():

    def __init__(self, indir=None, outdir=None, directory=None, filename=None, template=None):
        self.indir = indir
        self.outdir = outdir
        self.directory = directory
        self.filename = filename
        self.template = template
        self.title = None
        self.date = None
        self.leader = None
        self.body = None
        self.markup = None
        self.markdown = Markdown()

    def __repr__(self): # pragma: no cover
        return f'<Post: {self.filename}>'

    def read_file(self, directory, filename):
        '''
        How can skipping be best accomplished here? This doesn't actually work as
        intended because reading the non-existent file will throw a TypeError
        later in the procedure/chain. Need to bail out of this particular Post
        early.
        '''
        post_file = os.path.join(directory, filename)
        try:
            with open(post_file) as f:
                return f.read()
        except FileNotFoundError:
            logger.warning(f'{post_file} was not found, skipping!')

    def format_output(self):
        filename = slugify(self.title)
        return f'{filename}.html'

    def write_post(self):
        '''
        Is the call to `makedirs` is a little non-obvious? This method is very -
        stateful(?) - and requires a lot of mocking/patching to test
        '''
        relative_path = os.path.relpath(self.directory, self.indir)
        self.path = os.path.join(relative_path, self.format_output())
        output_path = os.path.join(self.outdir, self.path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(self.markup)

    def parse(self, raw_text):
        '''
        Parse a raw post into "frontmatter" (metadata) and the post body, splitting
        on an unlikely character sequence '+++'
        Args:
            raw_text: string contents of a post file
        '''
        try:
            frontmatter, body = re.split(r'^\+\+\+$', raw_text,
                                         maxsplit=1, flags=re.M)
            lines = (frontmatter.strip().split('\n'))
            line_pairs = (line.split(':', maxsplit=1) for line in lines)
            metadata = {key.strip().lower(): value.strip()
                        for key, value in line_pairs}
            self.title = metadata['title']
            self.date = (datetime
                         .strptime(metadata['date'], '%Y-%m-%d')
                         .replace(tzinfo=timezone.utc))
            self.body = body.strip()
            self.leader = self.parse_leader(self.body)
        except (ValueError, KeyError, TypeError) as e:
            raise ValueError(f'Unable to parse post from:\n{raw_text[:50]}')

    def parse_leader(self, post_body):
        '''
        I refer to the first paragraph of a post as a "leader" and like to extract
        it out automatically to generate an index page. Small idiosyncracy,
        Python's `re` module won't split on a zero-width match (e.g. `^$`) so
        we're splitting on the first two newlines ¯\_(ツ)_/¯
        Args:
            post_body: string/text of a post, stripped of frontmatter
        '''
        first_paragraph, *_ = post_body.strip().split('\n\n', maxsplit=1)
        return first_paragraph

    def render(self):
        '''
        a bit of a catch-all method
        '''
        self.leader = self.markdown(self.leader)
        self.body_markup = self.markdown(self.body)
        self.markup = self.template.render(post=self)
        return self.markup

    def create_post(self):
        '''
        wrapper method to simplify using the Post class from the Static class
        '''
        try:
            self.body = self.read_file(self.directory, self.filename)
            self.parse(self.body)
            self.render()
            self.write_post()
        except (ValueError, TypeError) as e:
            raise ValueError(e)


def slugify(text):
    '''
    Build hyphenated post slugs from "unsafe" text. RFC3986 requires percent
    encoding for UCS/unicode points.

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
