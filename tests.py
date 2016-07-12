import unittest

from static import StaticGenerator, slugify


class FunctionalTests(unittest.TestCase):
    config_file = "temp/config.json"

    def test_config(self):
        s = StaticGenerator(self.config_file)
        config = s.read_config_file()
        self.assertEqual(config["author"], "Test Author")

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

    def test_alphanumeric(self):
        input_string = "Contains: 3? illegal characters!"
        self.assertEqual(slugify(input_string),
                         "contains-3-illegal-characters")
        
    def test_quotes(self):
        input_string = "\"quoted phrase\" string's got an apostrophe"
        self.assertEqual(slugify(input_string),
                         "quoted-phrase-strings-got-an-apostrophe")

    def test_trailing_hyphens(self):
        input_string = "This would be pretty braindead--"
        self.assertEqual(slugify(input_string),
                         "this-would-be-pretty-braindead")

    def test_unicode_failure(self):
        """This should be fixed to accurately percent encode UTF-8 characters...
        eventually. I've yet to use unicode chars in post title, but WHO KNOWS

        """
        input_string = "düsseldorf motörhead"
        self.assertEqual(slugify(input_string), "d-sseldorf-mot-rhead")
