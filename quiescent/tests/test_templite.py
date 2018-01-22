# Tests for a code-generating template engine, taken from the book "500 Lines
# or Less", chapter 21: "A Template Engine"[0] by Ned Batchelder, except where it
# is different.
#
# - [0] http://aosabook.org/en/500L/a-template-engine.html
#
# MIT licensed:
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import re
from quiescent.templite import Templite, TempliteSyntaxError
from unittest import TestCase


class AnyOldObject:
    """
    Simple testing object.

    Use keyword arguments in the constructor to set attributes on the object.
    """

    def __init__(self, **attrs):
        for n, v in attrs.items():
            setattr(self, n, v)


class TempliteTest(TestCase):
    """Tests for Templite."""

    def try_render(self, text, ctx=None, result=None):
        """
        Render `text` through `ctx`, and it had better be `result`.

        Result defaults to None so we can shorten the calls where we expect an
        exception and never get to the result comparison.
        """
        actual = Templite(text).render(ctx or {})
        if result:
            self.assertEqual(actual, result)

    def assertSynErr(self, msg):
        pat = "^" + re.escape(msg) + "$"
        return self.assertRaisesRegex(TempliteSyntaxError, pat)

    def test_passthrough(self):
        # Strings without variables are passed through unchanged.
        self.assertEqual(Templite("Hello").render(), "Hello")
        self.assertEqual(
            Templite("Hello, 20% fun time!").render(),
            "Hello, 20% fun time!"
        )

    def test_variables(self):
        # Variables use {{var}} syntax.
        self.try_render("Hello, {{name}}!", {'name': 'Foo'}, "Hello, Foo!")

    def test_undefined_variables(self):
        # Using undefined names is an error.
        with self.assertRaises(Exception):
            self.try_render("Hi, {{name}}!")

    def test_reusability(self):
        '''A single Templite can be used more than once with different data.'''
        globs = {
            'punct': '!',
        }

        template = Templite("{{name.upper}}{{punct}}", globs)
        self.assertEqual(template.render({'name': 'Foo'}), "FOO!")
        self.assertEqual(template.render({'name': 'Bar'}), "BAR!")

    def test_attribute(self):
        # Variables' attributes can be accessed with dots.
        obj = AnyOldObject(a="Ay")
        self.try_render("{{obj.a}}", locals(), "Ay")

        obj2 = AnyOldObject(obj=obj, b="Bee")
        self.try_render("{{obj2.obj.a}} {{obj2.b}}", locals(), "Ay Bee")

    def test_member_function(self):
        # Variables' member functions can be used, as long as they are nullary.
        class WithMemberFns(AnyOldObject):
            """A class to try out member function access."""

            def ditto(self):
                """Return twice the .txt attribute."""
                return self.txt + self.txt
        obj = WithMemberFns(txt="Once")
        self.try_render("{{obj.ditto}}", locals(), "OnceOnce")

    def test_item_access(self):
        # Variables' items can be used.
        d = {'a': 17, 'b': 23}
        self.try_render("{{d.a}} < {{d.b}}", locals(), "17 < 23")

    def test_loops(self):
        # Loops work like in Django.
        nums = [1, 2, 3, 4]
        self.try_render(
            "Look: {% for n in nums %}{{n}}, {% endfor %}done.",
            locals(),
            "Look: 1, 2, 3, 4, done."
        )

        self.try_render(
            "Look: {% for n in nums %}{{n}}, {% endfor %}done.",
            locals(),
            "Look: 1, 2, 3, 4, done."
        )

    def test_empty_loops(self):
        self.try_render(
            "Empty: {% for n in nums %}{{n}}, {% endfor %}done.",
            {'nums': []},
            "Empty: done."
        )

    def test_multiline_loops(self):
        self.try_render(
            "Look: \n{% for n in nums %}\n{{n}}, \n{% endfor %}done.",
            {'nums': [1, 2, 3]},
            "Look: \n\n1, \n\n2, \n\n3, \ndone."
        )

    def test_multiple_loops(self):
        self.try_render(
            "{% for n in nums %}{{n}}{% endfor %} and "
            "{% for n in nums %}{{n}}{% endfor %}",
            {'nums': [1, 2, 3]},
            "123 and 123"
        )

    def test_if(self):
        self.try_render(
            "Hi, {% if foo %}FOO{% endif %}{% if bar %}BAR{% endif %}!",
            {'foo': 1, 'bar': 0},
            "Hi, FOO!"
        )
        self.try_render(
            "Hi, {% if foo %}FOO{% endif %}{% if bar %}BAR{% endif %}!",
            {'foo': 0, 'bar': 1},
            "Hi, BAR!"
        )
        self.try_render(
            "Hi, {% if foo %}FOO{% if bar %}BAR{% endif %}{% endif %}!",
            {'foo': 0, 'bar': 0},
            "Hi, !"
        )
        self.try_render(
            "Hi, {% if foo %}FOO{% if bar %}BAR{% endif %}{% endif %}!",
            {'foo': 1, 'bar': 0},
            "Hi, FOO!"
        )
        self.try_render(
            "Hi, {% if foo %}FOO{% if bar %}BAR{% endif %}{% endif %}!",
            {'foo': 1, 'bar': 1},
            "Hi, FOOBAR!"
        )

    def test_complex_if(self):
        class Complex(AnyOldObject):
            """A class to try out complex data access."""

            def getit(self):
                """Return it."""
                return self.it
        obj = Complex(it={'x': "Hello", 'y': 0})
        self.try_render(
            "@"
            "{% if obj.getit.x %}X{% endif %}"
            "{% if obj.getit.y %}Y{% endif %}"
            "{% if obj.getit.y %}S{% endif %}"
            "!",
            {'obj': obj, 'str': str},
            "@X!"
        )

    def test_loop_if(self):
        self.try_render(
            "@{% for n in nums %}{% if n %}Z{% endif %}{{n}}{% endfor %}!",
            {'nums': [0, 1, 2]},
            "@0Z1Z2!"
        )
        self.try_render(
            "X{%if nums%}@{% for n in nums %}{{n}}{% endfor %}{%endif%}!",
            {'nums': [0, 1, 2]},
            "X@012!"
        )
        self.try_render(
            "X{%if nums%}@{% for n in nums %}{{n}}{% endfor %}{%endif%}!",
            {'nums': []},
            "X!"
        )

    def test_nested_loops(self):
        self.try_render(
            "@"
            "{% for n in nums %}"
            "{% for a in abc %}{{a}}{{n}}{% endfor %}"
            "{% endfor %}"
            "!",
            {'nums': [0, 1, 2], 'abc': ['a', 'b', 'c']},
            "@a0b0c0a1b1c1a2b2c2!"
        )

    def test_exception_during_evaluation(self):
        # TypeError: Couldn't evaluate {{ foo.bar.baz }}:
        # 'NoneType' object is unsubscriptable
        with self.assertRaises(TypeError):
            self.try_render(
                "Hey {{foo.bar.baz}} there", {'foo': None}, "Hey ??? there"
            )

    def test_bad_names(self):
        with self.assertSynErr("Invalid name: var%&!@"):
            self.try_render("Wat: {{ var%&!@ }}")
        with self.assertSynErr("Invalid name: filter%&!@"):
            self.try_render("Wat: {{ filter%&!@ }}")
        with self.assertSynErr("Invalid name: @"):
            self.try_render("Wat: {% for @ in x %}{% endfor %}")

    def test_bogus_tag_syntax(self):
        with self.assertSynErr("Bad syntax:\n\t{% bogus %}"):
            self.try_render("Huh: {% bogus %}!!{% endbogus %}??")

    def test_malformed_if(self):
        with self.assertSynErr("Bad syntax:\n\t{% if %}"):
            self.try_render("Buh? {% if %}hi!{% endif %}")
        with self.assertSynErr("Bad syntax:\n\t{% if this or that %}"):
            self.try_render("Buh? {% if this or that %}hi!{% endif %}")

    def test_malformed_for(self):
        with self.assertSynErr("Bad syntax:\n\t{% for %}"):
            self.try_render("Weird: {% for %}loop{% endfor %}")
        with self.assertSynErr("Bad syntax:\n\t{% for x from y %}"):
            self.try_render("Weird: {% for x from y %}loop{% endfor %}")
        with self.assertSynErr("Bad syntax:\n\t{% for x, y in z %}"):
            self.try_render("Weird: {% for x, y in z %}loop{% endfor %}")

    def test_bad_nesting(self):
        with self.assertSynErr("Bad syntax, unmatched action:\n\tif"):
            self.try_render("{% if x %}X")
        with self.assertSynErr("Bad syntax:\n\t{% endfor %}"):
            self.try_render("{% if x %}X{% endfor %}")
        with self.assertSynErr("Bad syntax:\n\t{% endif %}"):
            self.try_render("{% if x %}{% endif %}{% endif %}")

    def test_malformed_end(self):
        with self.assertSynErr("Bad syntax:\n\t{% end if %}"):
            self.try_render("{% if x %}X{% end if %}")
        with self.assertSynErr("Bad syntax:\n\t{% endif now %}"):
            self.try_render("{% if x %}X{% endif now %}")
