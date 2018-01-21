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
import datetime

from quiescent.post import Post, slugify


class PostsTests(unittest.TestCase):

    def test_front_matter_parsing(self):
        leading_space = ('\n  title       :    test\ndate: 2017-01-01\n+++\n', 'test')
        mixed_case = ('\nTitle: test\nDate: 2017-01-01\n+++\n', 'test')
        correct = ('\ntitle: test\ndate: 2017-01-01\n+++\n', 'test')
        non_greedy = ('\ntitle:: test\ndate: 2017-01-01\n+++\n', ': test')
        for case, result in (leading_space, mixed_case, correct, non_greedy):
            with self.subTest():
                frontmatter, _ = Post._split(case)
                self.assertEqual(frontmatter['title'], result)

    def test_front_matter_parsing_negative(self):
        too_many = '\ntitle: test\ndate: 2017-01-01\n++++\n'
        too_few = '\ntitle: test\ndate: 2017-01-01\n++\n'
        post = Post()
        for i in (too_many, too_few):
            with self.subTest():
                with self.assertRaises(ValueError):
                    post.parse(i)

    def test_date_parsing(self):
        raw_text = '\ntitle: test\ndate: 2017-01-02\n+++\n'
        meta, _ = Post._split(raw_text)
        date = Post._parse_date(meta['date'])
        self.assertTrue(all([date.day == 2,
                             date.month == 1,
                             date.year == 2017]))

    def test_leader_parsing(self):
        leader = Post._parse_leader('\nfoo bar baz\n\nfoo bar baz\n')
        self.assertEqual(leader, 'foo bar baz')

    def test_post_parsing_leader(self):
        _, body = Post._split('\ntitle: test\ndate: 2017-01-01\n+++\nfoo \nfoo \n\nthe rest\n')
        leader = Post._parse_leader(body)
        self.assertEqual(leader, 'foo \nfoo ')

    def test_leader_parsing_single_paragraph(self):
        leader = Post._parse_leader('\nfoo bar baz\n')
        self.assertEqual(leader, 'foo bar baz')

    def test_sorting(self):
        earlier = Post().parse('\ntitle: test\ndate: 2016-01-01\n+++\nfoo\n')
        later = Post().parse('\ntitle: test\ndate: 2017-01-01\n+++\nbar\n')
        latest = Post().parse('\ntitle: test\ndate: 2017-01-02\n+++\nbaz\n')
        self.assertEqual(sorted([earlier, latest, later]),
                                [latest, later, earlier])


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
