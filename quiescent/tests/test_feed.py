# Copyright 2017 Nolan Prescott
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import unittest
from datetime import datetime

from quiescent.feed import feed
from quiescent.post import Post


class FeedTests(unittest.TestCase):

    def test_feed_string(self):
        '''
        Verify output against a known valid feed, verified with:
        https://validator.w3.org/feed/#validate_by_input
        '''
        self.maxDiff = None # for long diffs
        f = feed([], # no posts
                 date=datetime.strptime('12-2017-11', '%m-%Y-%d'),
                 name='test configuration',
                 domain='example.com',
                 feed_link='feed.xml',
                 feed_author='unit tester')
        expected_string = (
            '<feed xmlns="http://www.w3.org/2005/Atom">'
            '<title>test configuration</title>'
            '<link href="example.com" /><link href="example.com" rel="self" />'
            '<updated>2017-12-11T00:00:00</updated>'
            '<author><name>unit tester</name></author>'
            '<id>example.com</id>'
            '</feed>')
        self.assertEqual(f, expected_string)

    def test_posts_feed(self):
        self.maxDiff = None # for long diffs

        p = Post()
        p.title = 'First Post'
        p.date = datetime.strptime('12-2017-01', '%m-%Y-%d')
        p.body = '<h1>not much here</h1>'

        f = feed([p],
                 date=datetime.strptime('12-2017-11', '%m-%Y-%d'),
                 name='testing is important',
                 domain='example.com',
                 feed_link='feed.xml',
                 feed_author='fizz buzz')
        expected_string = ('<feed xmlns="http://www.w3.org/2005/Atom">'
                           '<title>testing is important</title>'
                           '<link href="example.com" /><link href="example.com" rel="self" />'
                           '<updated>2017-12-11T00:00:00</updated>'
                           '<author><name>fizz buzz</name></author>'
                           '<id>example.com</id>'
                           '<entry><title>First Post</title><link href="example.com" />'
                           '<id>example.com</id><updated>2017-12-01T00:00:00</updated>'
                           '<content type="html">&lt;h1&gt;not much here&lt;/h1&gt;</content></entry></feed>')
        self.assertEqual(f, expected_string)
