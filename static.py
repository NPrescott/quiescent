import json
import sys
import os
import re
from mistune import Markdown
from jinja2 import Environment, PackageLoader

# TODO: lots of functions/no-self use happening here
class StaticGenerator():
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self.read_config_file()
        self._separator = re.compile(r'^===$', re.MULTILINE)
        self.markdown = Markdown()

    def read_config_file(self):
        with open(self.config_file) as f:
            config = json.load(f)
        return config

    def read_file(self, filename):
        with open(filename) as f:
            contents = f.read()
        return contents

    def write_output_file(self, contents, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, mode='w', encoding='utf8') as outfile:
            outfile.write(contents)

    def templatize_post(self, contents):
        env = Environment(loader=PackageLoader('static', 'templates'))
        template = env.get_template('post.html')
        return template.render(post_body=contents)

    def collect_posts(self, from_dir):
        for root, _, files in os.walk(from_dir):
            for _file in files:
                if _file.endswith('.md'):
                    yield (root, _file)

    def parse_post(self, content):
        _split_contents = self._separator.split(content, maxsplit=1)
        if len(_split_contents) < 2:
            raise SyntaxError("Failed to parse Post header")
        header_string, post_body = _split_contents
        kv_string = header_string.strip().split('\n')
        header = {k: v.strip() for k,v in (i.split(':', maxsplit=1)
                                           for i in kv_string)}
        return header, post_body

    def create_posts(self):
        posts_dir = self.config['posts_dir']
        output_dir = self.config['output_dir']

        for directory, filename in self.collect_posts(posts_dir):
            post_file = os.path.join(directory, filename)
            raw_text = self.read_file(post_file)
            header, post_body = self.parse_post(raw_text)
            markup = self.markdown(post_body)
            templated_html = self.templatize_post(markup)
            _outdir = re.sub(posts_dir, output_dir, directory)
            _outfile = re.sub('.md', '.html', filename)
            out_path = os.path.join(_outdir, _outfile)
            self.write_output_file(templated_html, out_path)

if __name__ == '__main__':
    s = StaticGenerator()
    s.create_posts()
