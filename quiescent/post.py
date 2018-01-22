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
import functools
import urllib.parse
import os
import re

from mistune import Markdown


@functools.total_ordering
class Post:

    def __init__(self, relative_dir=''):
        self.relative_dir = relative_dir
        self.path = None
        self.title = None
        self._date = None
        self.date = None
        self.leader = None
        self.body = None
        self.markup = None
        self.markdown = Markdown()

    def __gt__(self, other):
        '''used for sorting, reverse chronologically'''
        return other._date > self._date

    def __eq__(self, other):
        '''
        this may be a bit ambiguous, but semantically, it seems like a post is
        "equal" to another if the text body is the same
        '''
        return self.body == other.body

    def __repr__(self):
        return f'<Post: {self.title}, {self.date}>'

    def parse(self, raw_text):
        '''
        Args:
            raw_text: string contents of a post file
        '''
        try:
            post = Post(relative_dir=self.relative_dir)
            meta, body = self._split(raw_text)
            post.title = meta['title']
            post.slug = slugify(post.title)
            post.path = os.path.join(self.relative_dir, f'{post.slug}.html')
            post._date = self._parse_date(meta['date'])
            post.date = post._date.strftime('%Y-%m-%d')
            post.body = self.markdown(body)
            post.leader = self.markdown(self._parse_leader(body))
            return post
        except (ValueError, KeyError, TypeError) as e:
            raise ValueError(f'Unable to parse post from:\n{raw_text[:50]}')

    @staticmethod
    def _split(text):
        '''
        Take as input text comprising a post file:

            title: some text
            date: 2015-12-01
            ++++
            ... post contents ...

        and return a tuple of a dictionary of the top "metadata" kv-pairs and
        a string of the rest of the file
        '''
        frontmatter, body = re.split(r'^\+\+\+$', text, maxsplit=1, flags=re.M)
        lines = frontmatter.strip().split('\n')
        line_pairs = (line.split(':', maxsplit=1) for line in lines)
        meta = {key.strip().lower(): value.strip()
                for key, value in line_pairs}
        return meta, body

    @staticmethod
    def _parse_date(text, date_spec='%Y-%m-%d'):
        return (datetime
                .strptime(text, date_spec)
                .replace(tzinfo=timezone.utc))

    @staticmethod
    def _parse_leader(post_body):
        '''
        I refer to the first paragraph of a post as a "leader" and like to extract
        it out automatically to generate an index page. Small idiosyncracy,
        Python's `re` module won't split on a zero-width match (e.g. `^$`) so
        we're splitting on the first two newlines ¯\_(ツ)_/¯
        Args:
            post_body: string, a post, stripped of frontmatter
        '''
        first_paragraph, *_ = (post_body
                               .strip() # excess whitespace
                               .split('\n\n', maxsplit=1))
        return first_paragraph


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
    # my kingdom for a pipe operator or a threading macro...
    _string = QUOTES.sub('', text)
    _string = _string.lower()
    _string = NOT_CHAR.sub('-', _string)
    _string = MULTIPLE_DASH.sub('-', _string)
    _string = urllib.parse.quote(_string, safe='-')
    output_string = _string.strip('-')

    return output_string
