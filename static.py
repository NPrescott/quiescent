from datetime import datetime
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
        self.all_posts = []

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

    def templatize_post(self, post):
        env = Environment(loader=PackageLoader('static', 'templates'))
        template = env.get_template('post.html')
        return template.render(post=post)

    def collect_posts(self, from_dir):
        for root, _, files in os.walk(from_dir):
            for _file in files:
                if _file.endswith('.md'):
                    yield (root, _file)

    def parse_post(self, content):
        post_obj = dict()
        _split_contents = self._separator.split(content, maxsplit=1)
        if len(_split_contents) < 2:
            raise SyntaxError("Failed to parse Post header")
        header_string, post_obj['body'] = _split_contents
        kv_string = header_string.strip().split('\n')
        post_obj['header'] = {k: v.strip() for k,v in (i.split(':', maxsplit=1)
                                           for i in kv_string)}
        if 'date' in post_obj['header']:
            post_obj['header']['date'] = datetime.strptime(post_obj['header']['date'], '%Y-%m-%d')
        return post_obj

    def create_posts(self):
        posts_dir = self.config['posts_dir']
        output_dir = self.config['output_dir']

        for directory, filename in self.collect_posts(posts_dir):
            post_file = os.path.join(directory, filename)
            raw_text = self.read_file(post_file)
            post = self.parse_post(raw_text)
            post['body'] = self.markdown(post['body'])
            templated_html = self.templatize_post(post)
            _outdir = re.sub(posts_dir, output_dir, directory)
            _outfile = re.sub('.md', '.html', filename)
            out_path = os.path.join(_outdir, _outfile)
            self.write_output_file(templated_html, out_path)
            self.all_posts.append(post)

        # I'm going to need to list of all posts in order by date for feed
        # generation and the index and archive pages don't have dates - I also
        # don't want them in the feed. So I'm pretending they are just *really*
        # old.
        #
        # Kind of a hack, alternatives include a 'non-feed' header option,
        # checking the index/archive titles before feed generation
        self.all_posts = sorted(self.all_posts,
                                key=lambda post:
                                post['header'].get('date',
                                                datetime.strptime('1970-01-01',
                                                                  '%Y-%m-%d')),
                                reverse=True)

    def create_feed(self):
        raise NotImplementedError

    def create_archive(self):
        raise NotImplementedError

if __name__ == '__main__':
    s = StaticGenerator()
    s.create_posts()
