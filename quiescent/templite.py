# A code-generating template engine, taken from the book "500 Lines or Less",
# chapter 21: "A Template Engine"[0] by Ned Batchelder, except where it is
# different.
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


class CodeBuilder:
    def __init__(self, indent=0):
        self.code = []
        self.current_indent = indent
        self.INDENT = 4

    def add_line(self, line):
        self.code.extend([' ' * self.current_indent, line, '\n'])

    def indent(self):
        self.current_indent += self.INDENT

    def dedent(self):
        self.current_indent -= self.INDENT

    def add_section(self):
        section = CodeBuilder(self.current_indent)
        self.code.append(section)
        return section

    def __str__(self):
        return ''.join(str(c) for c in self.code)

    def get_globals(self):
        assert self.current_indent == 0
        python_source = str(self)
        global_namespace = {}
        exec(python_source, global_namespace)
        return global_namespace


class TempliteSyntaxError(Exception):
    pass


class Templite:
    def __init__(self, text, *contexts):
        self.all_variables = set()
        self.loop_variables = set()
        self.context = {}
        for context in contexts:
            self.context.update(context)
        code = CodeBuilder()
        code.add_line('def render_function(context, do_dots):')
        code.indent()
        # where variables are extracted
        variable_code = code.add_section()
        code.add_line('result = []')
        # for tracking if/endif, for/endfor etc.
        operations_stack = []
        # omit comments, match either {{expression}} or {%action%} non-greedily
        tokens = re.split(r'(?s)({{.*?}}|{%.*?%})', text)

        for token in tokens:
            if token.startswith('{{'):
                expression = self._expr_code(token[2:-2].strip())
                code.add_line(f'result.append(str({expression}))')
            elif token.startswith('{%'):
                words = token[2:-2].strip().split()
                if words[0] == 'if':
                    if len(words) != 2:
                        raise TempliteSyntaxError(f'Bad syntax:\n\t{token}')
                    operations_stack.append('if')
                    code.add_line(f'if {self._expr_code(words[1])}:')
                    code.indent()
                elif words[0] == 'for':
                    if len(words) != 4 or words[2] != 'in':
                        raise TempliteSyntaxError(f'Bad syntax:\n\t{token}')
                    operations_stack.append('for')
                    self._variable(words[1], self.loop_variables)
                    code.add_line(
                        f'for c_{words[1]} in {self._expr_code(words[3])}:')
                    code.indent()
                elif words[0].startswith('end'):
                    if len(words) != 1:
                        raise TempliteSyntaxError(f'Bad syntax:\n\t{token}')
                    end_type = words[0].lstrip('end')
                    if not operations_stack:
                        raise TempliteSyntaxError(f'Bad syntax:\n\t{token}')
                    if end_type != operations_stack.pop():
                        raise TempliteSyntaxError(f'Bad syntax:\n\t{token}')
                    code.dedent()
                else:
                    raise TempliteSyntaxError(f'Bad syntax:\n\t{token}')
            else:
                if token:
                    code.add_line(f'result.append({repr(token)})')

        if operations_stack:
            raise TempliteSyntaxError(
                f'Bad syntax, unmatched action:\n\t{operations_stack[-1]}')

        for variable in self.all_variables - self.loop_variables:
            variable_code.add_line(f'c_{variable} = context[{repr(variable)}]')
        code.add_line("return ''.join(result)")
        code.dedent()
        self._render_function = code.get_globals()['render_function']

    def _expr_code(self, expression):
        if '.' in expression:
            dots = expression.split('.')
            code = self._expr_code(dots[0])
            args = ', '.join(repr(d) for d in dots[1:])
            code = f'do_dots({code}, {args})'
        else:
            self._variable(expression, self.all_variables)
            code = f'c_{expression}'
        return code

    def _variable(self, name, variable_set):
        if not re.match(r'[_a-zA-Z][_a-zA-Z0-9]*$', name):
            raise TempliteSyntaxError(f'Invalid name: {name}')
        variable_set.add(name)

    def render(self, context=None):
        render_context = dict(self.context)
        if context:
            render_context.update(context)
        return self._render_function(render_context, self._infer_properties)

    def _infer_properties(self, value, *properties):
        for prop in properties:
            try:
                value = getattr(value, prop)
            except AttributeError:
                value = value[prop]
            if callable(value):
                value = value()
        return value
