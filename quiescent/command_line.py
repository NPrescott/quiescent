import argparse

from .static import StaticGenerator

def main():
    parser = argparse.ArgumentParser(
        description=('Generate a collection of static HTML pages from a '
                     'collection of markdown documents'))
    parser.add_argument('-c', '--config', default='config.ini')

    args = parser.parse_args()
    s = StaticGenerator(config_file=args.config)
    s.configure()
    s.process_posts()
    s.write_generated_files()
    s.copy_media()
