Quiescent
=========

*Simplified static site generation*

Quiescent is a static site generator focused on eliminating complexity in
creating weblog-like sites. It is built around the idea of static assets and
plain-text, utilizing a hierarchical directory and URL structure for ease of
use in hyperlinking and deploying to web-servers. All *posts* are written in
`Markdown <https://daringfireball.net/projects/markdown/>`_, and later converted
to plain HTML, there is support for publishing static assets such as images or
JavaScript.

Quiescent does very little magic and aims only to simplify the annoying or
boring parts of site creation, so that the focus remains on content. As such,
the only parts of the resulting site that are automatically generated are the
`Atom feed <https://tools.ietf.org/html/rfc4287>`_, an index page, and an
*archive* of all posts.

Quiescent has been built with `Jinja2 <http://jinja.pocoo.org/>`_ for
templating, `Mistune <https://github.com/lepture/mistune>`_ for markdown
parsing, and Python 3.6 (for ``f``-string formatting).

Installation
------------

::

   pip install quiescent

Usage
-----

The interface to the program is through the ``quiescent`` command, which takes
an optional argument ``-c`` or ``--config``, to name a `configuration .ini
<https://docs.python.org/3/library/configparser.html>`_ file other than the
default ``config.ini``.

::

   cd blog-dir/
   quiescent --bootstrap  # initial configuration
   quiescent              # equivalent to quiescent --config config.ini

In order for the program to run as intended, the ``config.ini`` file must be
modified to suit the destination site.

The following templates are required and included in the ``bootstrap`` command
upon initial configuration:

 - archive.html
 - base.html
 - index.html
 - post.html

Tips for Writing
~~~~~~~~~~~~~~~~

All posts written require a title and a date using a specific format at the
beginning of the markdown file. The format is as follows:

::

   title: <post title>
   date: <must match the configured date format>
   +++

An important note to keep in mind when writing posts, the links used in
referencing local media (images, style sheets, etc.) are used directly in the
Atom feed, which may break relative URLs. A solution to this (and the author's
recommendation) is to specify a base URL and link relative to that, so that
links resolve correctly throughout the generated content of the site.

Publishing
~~~~~~~~~~

Due to the design of ``quiescent``, the contents and directory output from the
generation process is suitable for any basic web-server capable of serving
static files. In the case of the project author, after the site is *built*,
simply ``rsync``-ing the entire *build* directory is sufficient, for example:

::

   cd build-directory
   rsync -avz . user@example.com:/static/file/directory


Direction
~~~~~~~~~

Because of the wide variety of static site generators available this project
has a specific focus, with no plans to implement the following:

  - a local web-server
  - multiple input formats
  - comments
  - cross-post-to-twitter
  - tags

Development, Testing
~~~~~~~~~~~~~~~~~~~~

The project contains some unittests which are runnable using the ``setup.py``
command and require no additional dependencies or configuration.

::

   $ python setup.py -q test
   ..................
   ----------------------------------------------------------------------
   Ran 18 tests in 0.018s

   OK

License
-------
GPLv3, see COPYING for more information
