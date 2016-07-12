import unittest

from static import StaticGenerator, slugify


class FunctionalTests(unittest.TestCase):
    config_file = "temp/config.json"

    def test_config(self):
        s = StaticGenerator(self.config_file)
        config = s.read_config_file()
        self.assertEqual(config["author"], "Test Author")

    @unittest.expectedFailure
    def test_render_markdown(self):
        s = StaticGenerator(self.config_file)
        md = s.render_md_file("temp/test.md")
        
        self.assertEqual(asdf, '\
<h1>Title line, wow!</h1>\n\
<p>this is a paragraph</p>\n\
<ul>\n<li>bullet</li>\n\
<li>points</li>\n\
<li>yes</li>\n\
</ul>\n')

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
