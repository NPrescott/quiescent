# Copyright 2018 Nolan Prescott
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

"""
Atom feed[0] generator
  - update times are reported in UTC with no offset

[0]: https://tools.ietf.org/html/rfc4287
"""
import xml.etree.ElementTree as ET
from urllib.parse import urljoin


ET.register_namespace('', 'http://www.w3.org/2005/Atom')

def _feed(all_posts, date=None, name=None, domain=None, feed_link=None, feed_author=None):
    _feed = ET.Element('{http://www.w3.org/2005/Atom}feed')
    title = ET.SubElement(_feed, 'title')
    title.text = name
    link = ET.SubElement(_feed, 'link')
    link.attrib['href'] = domain
    feed_link = ET.SubElement(_feed, 'link')
    feed_link.attrib['href'] = urljoin(domain, feed_link)
    feed_link.attrib['rel'] = 'self'
    updated = ET.SubElement(_feed, 'updated')
    updated.text = date.isoformat()
    author = ET.SubElement(_feed, 'author')
    name = ET.SubElement(author, 'name')
    name.text = feed_author
    feed_id = ET.SubElement(_feed, 'id')
    feed_id.text = domain
    for post in all_posts:
        _feed_entry(_feed, post, domain=domain)
    return _feed

def _feed_entry(parent_element, post, domain=None):
    entry = ET.SubElement(parent_element, 'entry')
    title = ET.SubElement(entry, 'title')
    title.text = post.title
    link = ET.SubElement(entry, 'link')
    link.attrib['href'] = urljoin(domain, post.path)
    entry_id = ET.SubElement(entry, 'id')
    entry_id.text = urljoin(domain, post.path)
    updated = ET.SubElement(entry, 'updated')
    updated.text = post._date.isoformat()
    content = ET.SubElement(entry, 'content')
    content.attrib['type'] = 'html'
    content.text = post.body
    return entry

def feed(all_posts, date=None, name=None, domain=None, feed_link=None, feed_author=None):
    element = _feed(all_posts,
                    date=date,
                    name=name,
                    domain=domain,
                    feed_link=feed_link,
                    feed_author=feed_author)
    return ET.tostring(element, encoding='unicode')
