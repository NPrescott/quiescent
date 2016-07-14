import unittest
import datetime

from static import StaticGenerator, slugify


class StaticGeneratorTests(unittest.TestCase):
    config_file = "mock/config.json"
    s = StaticGenerator(config_file)
    config = s.read_config()

    def test_config(self):
        config = self.s.read_config()
        self.assertEqual(config["author"], "Test Author")

    def test_parse_date_exception(self):
        with self.assertRaises(TypeError):
            self.s.parse_date("2016/01/01")

    def test_parse_date(self):
        result = self.s.parse_date("2016-01-01")
        self.assertEqual(type(result), datetime.datetime)

    def test_split_post_exception(self):
        bad_text = "an improper post body"
        with self.assertRaises(TypeError):
            self.s.split_post(bad_text)

    def test_split_post_length(self):
        poorly_formatted_text = "===\n missing a header, post body okay"
        result = self.s.split_post(poorly_formatted_text)
        self.assertEqual(len(result), 2)

    def test_split_post_multiple(self):
        extra_header_text = "===\n missing header\n===\nweird text"
        result = self.s.split_post(extra_header_text)
        self.assertEqual(len(result), 2)

    def test_post_parts_header(self):
        title_date_string = "title: a title\ndate: 2016-01-01"
        body_string = "some long\npiece of text\nwould go here"
        result = self.s.parse_post_parts(title_date_string, body_string)
        self.assertTrue('title' in result)
        self.assertTrue('date' in result)

    def test_post_parts_misformatted(self):
        title_date_string = "title: a title\n 2016-01-01" # missing 'date:'
        body_string = "some long\npiece of text\nwould go here"
        with self.assertRaises(TypeError):
            self.s.parse_post_parts(title_date_string, body_string)

    def test_parse_header_failure(self):
        bad_header_text = "===\n missing header\n===\nweird text"
        with self.assertRaises(TypeError):
            self.s.parse_post_parts(bad_header_text)

    def test_parse_header_failure_message(self):
        bad_header_text = "title some title\ndate 2016-01-01===\n missing header\n===\nweird text"
        body_string = "some long\npiece of text\nwould go here"
        with self.assertRaisesRegex(TypeError, "Improperly formatted header: .*"):
            self.s.parse_header(bad_header_text)

    def test_post_template(self):
        post = {'title': 'amazing title',
                'body': '<p>some long text</p>'}
        result_html = self.s.templatize_post(post)
        self.assertEqual(result_html, 'amazing title\n\n<p>some long text</p>')

    def test_post_template_has_date(self):
        post = {'title': 'amazing title',
                'date': datetime.datetime(2016, 1, 1, 0, 0),
                'body': '<p>some long text</p>'}
        result_html = self.s.templatize_post(post)
        self.assertEqual(result_html,
                         'amazing title\n\n2016-01-01\n\n<p>some long text</p>')

class SlugifyTests(unittest.TestCase):
    def test_lowercase(self):
        input_string = "This Is A Title"
        self.assertEqual(slugify(input_string), "this-is-a-title")

    def test_punctuation(self):
        first_string = "Contains: 3? illegal characters!"
        self.assertEqual(slugify(first_string),
                         "contains-3-illegal-characters")

        second_string = "What is 1% of 20% of a question mark?"
        self.assertEqual(slugify(second_string), "what-is-1-of-20-of-a-question-mark")
        
    def test_quotes(self):
        input_string = "\"quoted phrase\" string's got an apostrophe"
        self.assertEqual(slugify(input_string),
                         "quoted-phrase-strings-got-an-apostrophe")

    def test_trailing_hyphens(self):
        input_string = "This would be pretty braindead--"
        self.assertEqual(slugify(input_string),
                         "this-would-be-pretty-braindead")

    def test_unicode(self):
        first_string = "Düsseldorf is a city in Germany"
        self.assertEqual(slugify(first_string), "d%C3%BCsseldorf-is-a-city-in-germany")

        second_string = "Let Over λ"
        self.assertEqual(slugify(second_string), "let-over-%CE%BB")
