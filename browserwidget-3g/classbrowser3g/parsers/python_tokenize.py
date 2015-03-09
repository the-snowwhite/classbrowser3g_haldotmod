# -*- coding: utf-8 -*-

#  Copyright © 2013  B. Clausius <barcc@gmx.de>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function, division

import token, tokenize

try:
    from . import ClassParserInterface, register_parser
except (ImportError, ValueError):
    ClassParserInterface = object
    register_parser = None

# http://docs.python.org/3/reference/grammar.html

class PythonParserTokenize (ClassParserInterface):
    def readline_textiter(self):
        next_line = self.current_line.copy()
        next_line.forward_line()
        text = self.current_line.get_text(next_line)
        self.current_line = next_line
        return text
        
    def parse(self, doc, location, model):
        if model is None:
            class Model(list):
                def append(self, titer, *args):
                    children = Model()
                    if titer is None:
                        titer = self
                    list.append(titer, (args, children))
                    return children
            model = Model()
            def print_tree(tree=model, indent=0):
                for item, children in tree:
                    print('  '*indent, item, sep='')
                    print_tree(children, indent+1)
            uri = location
            readline = doc.readline
        else:
            print_tree = lambda: None
            uri = location and location.get_uri()
            readline = self.readline_textiter
            self.current_line = doc.get_start_iter()
        self.titer = None
        token_iter = tokenize.generate_tokens(readline)
        # ttype, tstring, spos, epos, line
        # ttype, tstring, (srow, scol), (erow, ecol), line
        self.prev_token = token.ENDMARKER, '', (0, 0), (0, 0), ''
        self.last_token = None
        self.imports = []
        self.import_pos = None
        self.varnames = []
        self.isnamespace = True
        
        def _typecode_access(name, typecode):
            if name.startswith('__') and not name.endswith('__'):
                return typecode + '_priv'
            if name.startswith('_'):
                return typecode + '_prot'
            return typecode
            
        def _append_imports():
            if self.import_pos is not None:
                if len(self.imports) > 2:
                    titer = model.append(self.titer, 'import', 'namespace', uri, *self.import_pos)
                else:
                    titer = self.titer
                for imp in self.imports:
                    model.append(titer, *imp)
                self.imports = []
                self.import_pos = None
        def get_token():
            if self.last_token is None:
                self.last_token = next(token_iter)
                while self.last_token[0] in [tokenize.COMMENT, tokenize.NL]:
                    self.last_token = next(token_iter)
                if self.last_token[0] == tokenize.ERRORTOKEN:
                    srow, scol = self.last_token[2]
                    errstring = ''
                    while self.last_token[0] == tokenize.ERRORTOKEN:
                        erow, ecol = self.last_token[3]
                        errstring += self.last_token[1]
                        self.last_token = next(token_iter)
                    model.append(self.titer, '<%s>'%errstring, 'error', uri, srow, scol, erow, ecol)
                self.prev_token = self.last_token
            return self.last_token
        def pop_token():
            try:
                return get_token()
            finally:
                self.last_token = None
                
        # parse functions follow the Python 2 grammar loosely
        # http://docs.python.org/release/2.7.3/reference/grammar.html
        def parse_file_input():
            try:
                while True:
                    if parse_ttype(token.ENDMARKER):
                        return
                    if parse_ttype(token.NEWLINE) or parse_stmt():
                        continue
                    return
            finally:
                _append_imports()
        def parse_decorator():
            if parse_tstring('@'):
                parse_to_newline()
                return True
            return False
        def parse_decorators():
            if parse_decorator():
                while parse_decorator():
                    pass
                return True
            return False
        def parse_decorated():
            if parse_decorators():
                return parse_classdef() or parse_funcdef()
            return False
        def parse_classdef():
            ttype, tstring, (srow, scol), (erow, ecol), line = get_token()
            if parse_tstring('class'):
                _append_imports()
                name = parse_token_name()
                isnamespace = self.isnamespace
                self.isnamespace = True
                varnames = self.varnames
                self.varnames = []
                titer = self.titer
                typecode = _typecode_access(name, 'class')
                self.titer = model.append(titer, name, typecode, uri, srow, scol)
                ttype, tstring, (srow, scol), (erow, ecol), line = get_token()
                ecol = line.find(':')
                parse_to_string(':')
                parse_suite()
                _append_imports()
                self.titer = titer
                self.varnames = varnames
                self.isnamespace = isnamespace
                return True
            return False
        def parse_funcdef():
            ttype, tstring, (srow, scol), (erow, ecol), line = get_token()
            if parse_tstring('def'):
                _append_imports()
                name = parse_token_name()
                isnamespace = self.isnamespace
                self.isnamespace = False
                titer = self.titer
                typecode = _typecode_access(name, 'function')
                self.titer = model.append(titer, name, typecode, uri, srow, scol)
                parse_to_string(':')
                parse_suite()
                _append_imports()
                self.titer = titer
                self.isnamespace = isnamespace
                return True
            return False
        def parse_stmt():
            if get_token()[0] == token.DEDENT:
                return False
            return parse_compound_stmt() or parse_simple_stmt()
        def parse_simple_stmt():
            if parse_small_stmt():
                while parse_tstring(';'):
                    parse_small_stmt()
                if not parse_ttype(token.NEWLINE) and get_token()[0] not in [token.DEDENT, token.ENDMARKER]:
                    model.append(self.titer, '<error in statement>', 'error', uri, *get_token()[2])
                    parse_to_newline()
                return True
            return False
        def parse_small_stmt():
            if parse_tstring('pass') or parse_tstring('break') or parse_tstring('continue'):
                return True
            if parse_import_stmt():
                return True
            if (parse_tstring('print') or parse_tstring('del') or
                    parse_tstring('return') or parse_tstring('raise') or parse_tstring('yield') or
                    parse_tstring('global') or parse_tstring('exec') or parse_tstring('assert')):
                ntype, nstring = get_token()[:2]
                while ntype not in [token.NEWLINE, token.DEDENT, token.ENDMARKER] and nstring != ';':
                    self.last_token = None
                    ntype, nstring = get_token()[:2]
                return True
            return parse_expr_stmt()
        def parse_expr_stmt():
            ntype, nstring = get_token()[:2]
            if ntype in [token.NEWLINE, token.ENDMARKER] or nstring == ';':
                return False
            self.varrows = []
            while parse_testlist_left() and parse_tstring('='):
                if self.varrows:
                    _append_imports()
                    while self.varrows:
                        varrow = self.varrows.pop(0)
                        if varrow[0] not in self.varnames:
                            self.varnames.append(varrow[0])
                            model.append(self.titer, *varrow)
            srow, scol = self.prev_token[2]
            try:
                return parse_expr_stmt_rest()
            except tokenize.TokenError as e:
                model.append(self.titer, '<%s>'%e.args[0], 'error', uri, srow, scol)
                return False
        def parse_expr_stmt_rest():
            ntype, nstring = get_token()[:2]
            while ntype not in [token.NEWLINE, token.ENDMARKER] and nstring != ';':
                self.last_token = None
                ntype, nstring = get_token()[:2]
            return True
        def parse_testlist_left():
            if parse_test_left():
                while parse_tstring(','):
                    if not parse_test_left():
                        return False
                return True
            return False
        def parse_test_left():
            srow, scol = self.prev_token[2]
            try:
                if parse_tstring('('):
                    return parse_testlist_left() and parse_tstring(')')
                if parse_tstring('['):
                    return parse_testlist_left() and parse_tstring(']')
            except tokenize.TokenError as e:
                model.append(self.titer, '<%s>'%e.args[0], 'error', uri, srow, scol)
            ttype, tstring, (srow, scol), (erow, ecol), line = pop_token()
            if ttype == token.NAME:
                if tstring == 'self': # self.attrname = ...
                    if parse_tstring('.'):
                        ttype, tstring, spos, (erow, ecol), line = get_token()
                        if ttype == token.NAME:
                            self.last_token = None
                            typecode = _typecode_access(tstring, 'field')
                            self.varrows.append((tstring, typecode, uri, srow, scol, erow, ecol))
                            return True
                elif self.isnamespace: # name = ... in global namespace
                    typecode = _typecode_access(tstring, 'field')
                    self.varrows.append((tstring, typecode, uri, srow, scol, erow, ecol))
                    return True
                else:
                    return True
            return False
            tstring = get_token()[1]
            while not tstring.endswith('=') and tstring != ',' and ttype != token.NEWLINE:
                pop_token()
            return True
        def parse_import_stmt():
            pos = get_token()[2]
            if parse_tstring('import'): # import_name
                if self.import_pos is None:
                    self.import_pos = pos
                parse_dotted_as_names()
                return True
            if parse_tstring('from'): # import_from
                if self.import_pos is None:
                    self.import_pos = pos
                name = ''
                while parse_tstring('...'): # '...' is tokenized as ELLIPSIS
                    name += '...'
                while parse_tstring('.'):
                    name += '.'
                if get_token()[1] != 'import':
                    name += parse_dotted_name()
                parse_tstring('import')
                if parse_tstring('*'):
                    (srow, scol), (erow, ecol) = get_token()[2:4]
                    name = '* (from %s)' % name
                    self.imports.append((name, 'namespace', uri, srow, scol, erow, ecol))
                elif parse_tstring('('):
                    parse_import_as_names(name)
                    parse_tstring(')')
                else:
                    parse_import_as_names(name)
                return True
            return False
        def parse_import_as_name(dottedname):
            srow, scol = get_token()[2]
            name = parse_token_name()
            if parse_tstring('as'):
                name = '{} ({} from {})'.format(parse_token_name(), name, dottedname)
            else:
                name = '{} (from {})'.format(name, dottedname)
            erow, ecol = get_token()[2]
            self.imports.append((name, 'namespace', uri, srow, scol, erow, ecol))
        def parse_dotted_as_name():
            srow, scol = get_token()[2]
            name = parse_dotted_name()
            if parse_tstring('as'):
                name = '{} ({})'.format(parse_token_name(), name)
            erow, ecol = get_token()[2]
            self.imports.append((name, 'namespace', uri, srow, scol, erow, ecol))
        def parse_import_as_names(dottedname):
            parse_import_as_name(dottedname)
            while parse_tstring(','):
                parse_import_as_name(dottedname)
        def parse_dotted_as_names():
            parse_dotted_as_name()
            while parse_tstring(','):
                parse_dotted_as_name()
        def parse_dotted_name():
            names = [parse_token_name()]
            while parse_tstring('.'):
                names.append(parse_token_name())
            return '.'.join(names)
        def parse_compound_stmt():
            return (parse_if_stmt() or parse_while_stmt() or parse_for_stmt() or
                    parse_try_stmt() or parse_with_stmt() or
                    parse_funcdef() or parse_classdef() or parse_decorated())
        def parse_if_stmt():
            if parse_tstring('if'):
                parse_to_string(':')
                parse_suite()
                while parse_tstring('elif'):
                    parse_to_string(':')
                    parse_suite()
                if parse_tstring('else'):
                    parse_tstring(':')
                    parse_suite()
                return True
            return False
        def parse_while_stmt():
            if parse_tstring('while'):
                parse_to_string(':')
                parse_suite()
                if parse_tstring('else'):
                    parse_tstring(':')
                    parse_suite()
                return True
            return False
        def parse_for_stmt():
            if parse_tstring('for'):
                parse_to_string(':')
                parse_suite()
                if parse_tstring('else'):
                    parse_tstring(':')
                    parse_suite()
                return True
            return False
        def parse_try_stmt():
            if parse_tstring('try'):
                parse_tstring(':')
                parse_suite()
                while parse_tstring('except'):
                    parse_to_string(':')
                    parse_suite()
                if parse_tstring('else'):
                    parse_tstring(':')
                    parse_suite()
                if parse_tstring('finally'):
                    parse_tstring(':')
                    parse_suite()
                return True
            return False
        def parse_with_stmt():
            if parse_tstring('with'):
                parse_to_string(':')
                parse_suite()
                return True
            return False
        def parse_suite():
            if parse_simple_stmt():
                return True
            parse_ttype(token.NEWLINE)
            parse_ttype(token.INDENT)
            while parse_stmt():
                pass
            parse_ttype(token.DEDENT)
            return True
            
        def parse_token_name():
            ntype, nstring = get_token()[:2]
            if ntype == token.NAME:
                self.last_token = None
                return nstring
            return '<%s>' % token.tok_name[ntype]
        def parse_ttype(ttype):
            ntype = get_token()[0]
            if ttype == ntype:
                self.last_token = None
                return True
            return False
        def parse_tstring(tstring):
            nstring = get_token()[1]
            if tstring == nstring:
                self.last_token = None
                return True
            return False
        def parse_to_string(tstring):
            nstring = pop_token()[1]
            while tstring != nstring:
                if nstring == '(':
                    parse_to_string(')')
                elif nstring == '[':
                    parse_to_string(']')
                elif nstring == '{':
                    parse_to_string('}')
                nstring = pop_token()[1]
            return True
        def parse_to_newline():
            while pop_token()[0] != token.NEWLINE:
                pass
            return True
            
        try:
            parse_file_input()
        except StopIteration:
            (srow, scol), (erow, ecol) = self.prev_token[2:4]
            model.append(None, '<unexpected end>', 'error', uri, srow, scol, erow, ecol)
        except (IndentationError, tokenize.TokenError) as e:
            (srow, scol), (erow, ecol) = self.prev_token[2:4]
            model.append(None, '<%s>'%e, 'error', uri, srow, scol, erow, ecol)
            
        print_tree()
        
        
if register_parser is None:
    def main():
        import sys
        try:
            filename = sys.argv[1]
        except IndexError:
            parser = PythonParserTokenize()
            parser.parse(sys.stdin, None, None)
        else:
            with open(filename, 'rb') as pyfile:
                parser = PythonParserTokenize()
                parser.parse(pyfile, filename, None)
    if __name__ == '__main__':
        main()
else:
    register_parser(PythonParserTokenize.__name__, PythonParserTokenize, ['python', 'python3'],
                    'Python Parser (tokenize)',
                    '''Parser using the Python tokenize module''')
                
    

