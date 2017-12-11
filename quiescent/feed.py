# Copyright 2017 Nolan Prescott
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

"""Atom feed generator
----------------------

Revamping the (broken) feed generation capabilities in Static, I'm opting for
Atom because it seemed simpler, but I haven't read either spec entirely[0]. I'm
finally dropping all attempts at string-templating because, well, string
templates and XML :(

First pass here does the simplest thing and is relatively feature-less.
  - update times are reported in UTC with no offset

----------------------------------------
[0]: https://tools.ietf.org/html/rfc4287
"""
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import urljoin
import logging


logger = logging.getLogger(__name__)
ET.register_namespace('', 'http://www.w3.org/2005/Atom')

def feed(all_posts, **config):
    try:
        feed = ET.Element('{http://www.w3.org/2005/Atom}feed')
        title = ET.SubElement(feed, 'title')
        title.text = config['name']
        link = ET.SubElement(feed, 'link')
        link.attrib['href'] = config['domain']
        feed_link = ET.SubElement(feed, 'link')
        feed_link.attrib['href'] = urljoin(config['domain'], config['feed link'])
        feed_link.attrib['rel'] = 'self'
        updated = ET.SubElement(feed, 'updated')
        updated.text = datetime.now(timezone.utc).isoformat()
        author = ET.SubElement(feed, 'author')
        name = ET.SubElement(author, 'name')
        name.text = config['author']
        feed_id = ET.SubElement(feed, 'id')
        feed_id.text = config['domain']
        for post in all_posts:
            feed_entry(feed, post, domain=config['domain'])
        return feed
    except KeyError as e:
        raise KeyError(f"Configuration missing entry for: {e}")

def feed_entry(parent_element, post, domain=None):
    entry = ET.SubElement(parent_element, 'entry')
    title = ET.SubElement(entry, 'title')
    title.text = post.title
    link = ET.SubElement(entry, 'link')
    link.attrib['href'] = urljoin(domain, post.path)
    entry_id = ET.SubElement(entry, 'id')
    entry_id.text = urljoin(domain, post.path)
    updated = ET.SubElement(entry, 'updated')
    updated.text = post.date.isoformat()
    content = ET.SubElement(entry, 'content')
    content.attrib['type'] = 'html'
    content.text = post.body_markup
    return entry

def render_feed(feed_element):
    return ET.tostring(feed_element, encoding='utf-8')
