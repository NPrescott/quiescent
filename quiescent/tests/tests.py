# Copyright 2016 Nolan Prescott
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
from unittest import mock
import datetime
from jinja2 import Template

from quiescent.static import StaticGenerator
from quiescent.post import Post, slugify


class StaticGeneratorTests(unittest.TestCase):
    def test_post_sorting(self):
        earlier, later, latest = (Post(), Post(), Post())
        earlier.parse('\ntitle: test\ndate: 2016-01-01\n+++\nfoo\n')
        later.parse('\ntitle: test\ndate: 2017-01-01\n+++\nbar\n')
        latest.parse('\ntitle: test\ndate: 2017-01-02\n+++\nbaz\n')
        date_ordered = StaticGenerator().sort_posts_by_date([latest, earlier, later])
        self.assertEqual(date_ordered, [latest, later, earlier])


class PostsTests(unittest.TestCase):

    def test_front_matter_parsing(self):
        leading_space = '\n  title       :    test\ndate: 2017-01-01\n+++\n'
        mixed_case = '\nTitle: test\nDate: 2017-01-01\n+++\n'
        properly_formatted = '\ntitle: test\ndate: 2017-01-01\n+++\n'
        for case in (leading_space, mixed_case, properly_formatted):
            with self.subTest():
                post = Post()
                post.parse(case)
                self.assertEqual(post.title, 'test')

    def test_front_matter_parsing_nongreedy(self):
        excess_colons = '\ntitle:: test\ndate: 2017-01-01\n+++\n'
        post = Post()
        post.parse(excess_colons)
        self.assertEqual(post.title, ': test')

    def test_front_matter_parsing_negative(self):
        too_many = '\ntitle: test\ndate: 2017-01-01\n++++\n'
        too_few = '\ntitle: test\ndate: 2017-01-01\n++\n'
        post = Post()
        for i in (too_many, too_few):
            with self.subTest():
                with self.assertRaises(ValueError):
                    post.parse(i)

    def test_date_parsing(self):
        raw_text = '\ntitle: test\ndate: 2017-01-01\n+++\n'
        post = Post()
        post.parse(raw_text)
        self.assertEqual(type(post.date), datetime.datetime)

    def test_date_parsing_negative(self):
        wrong_format = '\ntitle: test\ndate: 2017-31-01\n+++\n'
        missing_date = '\ntitle: test\n+++\n'
        post = Post()
        for case in (wrong_format, missing_date):
            with self.subTest():
                with self.assertRaises(ValueError):
                    post.parse(case)

    def test_leader_parsing(self):
        leader = Post().parse_leader('\nfoo bar baz\n\nfoo bar baz\n')
        self.assertEqual(leader, 'foo bar baz')

    def test_post_parsing_leader(self):
        post = Post()
        post.parse('\ntitle: test\ndate: 2017-01-01\n+++\nfoo \nfoo \n\nthe rest\n')
        post.parse_leader(post.body)
        self.assertEqual(post.leader, 'foo \nfoo ')

    def test_leader_parsing_single_paragraph(self):
        leader = Post().parse_leader('\nfoo bar baz\n')
        self.assertEqual(leader, 'foo bar baz')

    def test_read_file_missing(self):
        with self.assertLogs():
            Post().read_file('2017', 'missing-post.md')

    def test_format_output(self):
        p = Post()
        p.parse('\ntitle: test\ndate: 2017-01-01\n+++\n')
        self.assertEqual(p.format_output(), 'test.html')

    def test_templating(self):
        '''
        not a great test, mostly a wrapper around `render`. Should this do more
        validation on the template? -- a bit overkill?
        '''
        t = Template('<div>{{post.body_markup}}</div>')
        post = Post(template=t)
        raw_text = '\ntitle: test\ndate: 2016-01-01\n+++\nfoo bar baz'
        post.parse(raw_text)
        post.render()
        # not exactly pretty but the markdown parser includes some errant
        # newlines here and there
        self.assertEqual(post.markup, '<div><p>foo bar baz</p>\n</div>')

    @mock.patch('quiescent.post.os.makedirs')
    def test_write_post(self, *args):
        '''
        I'm not sure how mock and patch work exactly...
        '''
        m = mock.mock_open()
        with mock.patch('builtins.open', m):
            post = Post(indir='posts', outdir='build', directory='posts/2017')
            post.title = 'A Post Title'
            post.markup = 'foo bar baz'
            post.write_post()
            m.assert_called_once_with('build/2017/a-post-title.html', 'w')
            handle = m()
            handle.write.assert_called_once_with('foo bar baz')


class SlugifyTests(unittest.TestCase):
    def test_lowercase(self):
        self.assertEqual(
            slugify('This Is A Title'),
            'this-is-a-title')

    def test_punctuation(self):
        self.assertEqual(
            slugify('Contains: 3? illegal characters!'),
            'contains-3-illegal-characters')

        self.assertEqual(
            slugify('What is 1% of 20% of a question mark?'),
            'what-is-1-of-20-of-a-question-mark')

    def test_quotes(self):
        self.assertEqual(
            slugify('\"quoted phrase\" string\'s got an apostrophe'),
            'quoted-phrase-strings-got-an-apostrophe')

    def test_trailing_hyphens(self):
        self.assertEqual(
            slugify('This would be pretty braindead--'),
            'this-would-be-pretty-braindead')

    def test_unicode(self):
        self.assertEqual(
            slugify('Düsseldorf is a city in Germany'),
            'd%C3%BCsseldorf-is-a-city-in-germany')

        self.assertEqual(
            slugify('Let Over λ'),
            'let-over-%CE%BB')
