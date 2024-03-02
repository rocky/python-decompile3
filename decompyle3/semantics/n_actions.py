#  Copyright (c) 2022-2024 by Rocky Bernstein
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
"""
Custom Nonterminal action functions. See NonterminalActions docstring.
"""

from spark_parser.ast import GenericASTTraversalPruningException
from xdis import iscode

from decompyle3.parsers.treenode import SyntaxTree
from decompyle3.scanners.tok import Token
from decompyle3.semantics.consts import (
    INDENT_PER_LEVEL,
    NO_PARENTHESIS_EVER,
    NONE,
    PARENTHESIS_ALWAYS,
    PRECEDENCE,
    minint,
)
from decompyle3.semantics.helper import flatten_list
from decompyle3.semantics.make_function36 import make_function36
from decompyle3.util import better_repr


class NonterminalActions:
    """
    Methods here all start with n_ and the remaining portion should be a nonterminal
    name defined by some rule.

    These methods take priority over names defined in table constants.
    All of the methods should have the same signature: (self, node) and return None.

    node is the subtree of the parse tree the that nonterminal name as the root.
    """

    def n_alias(self, node: SyntaxTree):
        if self.version <= (2, 1):
            if len(node) == 2:
                store = node[1]
                assert store == "store"
                if store[0].pattr == node[0].pattr:
                    self.write("import %s\n" % node[0].pattr)
                else:
                    self.write("import %s as %s\n" % (node[0].pattr, store[0].pattr))
                    pass
                pass
            self.prune()  # stop recursing

        store_node = node[-1][-1]
        assert store_node.kind.startswith("STORE_")
        iname = node[0].pattr  # import name
        sname = store_node.pattr  # store_name
        if iname and iname == sname or iname.startswith(sname + "."):
            self.write(iname)
        else:
            self.write(iname, " as ", sname)
        self.prune()  # stop recursing

    n_alias37 = n_alias

    def n_assign(self, node: SyntaxTree):
        # A horrible hack for Python 3.0 .. 3.2
        if (3, 0) <= self.version <= (3, 2) and len(node) == 2:
            if (
                node[0][0] == "LOAD_FAST"
                and node[0][0].pattr == "__locals__"
                and node[1][0].kind == "STORE_LOCALS"
            ):
                self.prune()
        self.default(node)

    def n_assign2(self, node: SyntaxTree):
        for n in node[-2:]:
            if n[0] == "unpack":
                n[0].kind = "unpack_w_parens"
        self.default(node)

    def n_assign3(self, node: SyntaxTree):
        for n in node[-3:]:
            if n[0] == "unpack":
                n[0].kind = "unpack_w_parens"
        self.default(node)

    def n_attribute(self, node: SyntaxTree):
        if node[0] == "LOAD_CONST" or node[0] == "expr" and node[0][0] == "LOAD_CONST":
            # FIXME: I didn't record which constants parenthesis is
            # necessary. However, I suspect that we could further
            # refine this by looking at operator precedence and
            # eval'ing the constant value (pattr) and comparing with
            # the type of the constant.
            node.kind = "attribute_w_parens"
        self.default(node)

    def n_bin_op(self, node: SyntaxTree):
        """bin_op (formerly "binary_expr") is the Python AST BinOp"""
        self.preorder(node[0])
        self.write(" ")
        self.preorder(node[-1])
        self.write(" ")
        # Try to avoid a trailing parentheses by lowering the priority a little
        self.prec -= 1
        self.preorder(node[1])
        self.prec += 1
        self.prune()

    def n_build_slice2(self, node: SyntaxTree):
        p = self.prec
        self.prec = NO_PARENTHESIS_EVER
        if not node[0].isNone():
            self.preorder(node[0])
        self.write(":")
        if not node[1].isNone():
            self.preorder(node[1])
        self.prec = p
        self.prune()  # stop recursing

    def n_build_slice3(self, node: SyntaxTree):
        p = self.prec
        self.prec = NO_PARENTHESIS_EVER
        if not node[0].isNone():
            self.preorder(node[0])
        self.write(":")
        if not node[1].isNone():
            self.preorder(node[1])
        self.write(":")
        if not node[2].isNone():
            self.preorder(node[2])
        self.prec = p
        self.prune()  # stop recursing

    def n_classdef(self, node: SyntaxTree):
        self.n_classdef36(node)

        # class definition ('class X(A,B,C):')
        cclass = self.currentclass

        # Pick out various needed bits of information
        # * class_name - the name of the class
        # * subclass_info - the parameters to the class  e.g.
        #      class Foo(bar, baz)
        #             -----------
        # * subclass_code - the code for the subclass body

        if node == "classdefdeco2":
            build_class = node
        else:
            build_class = node[0]
        build_list = build_class[1][0]
        if hasattr(build_class[-3][0], "attr"):
            subclass_code = build_class[-3][0].attr
            class_name = build_class[0].pattr
        elif (
            build_class[-3] == "mkfunc"
            and node == "classdefdeco2"
            and build_class[-3][0] == "load_closure"
        ):
            subclass_code = build_class[-3][1].attr
            class_name = build_class[-3][0][0].pattr
        elif hasattr(node[0][0], "pattr"):
            subclass_code = build_class[-3][1].attr
            class_name = node[0][0].pattr
        else:
            raise RuntimeError("Internal Error n_classdef: cannot find class name")

        if node == "classdefdeco2":
            self.write("\n")
        else:
            self.write("\n\n")

        self.currentclass = str(class_name)
        self.write(self.indent, "class ", self.currentclass)

        self.print_super_classes(build_list)
        self.println(":")

        # class body
        self.indent_more()
        self.build_class(subclass_code)
        self.indent_less()

        self.currentclass = cclass
        if len(self.param_stack) > 1:
            self.write("\n\n")
        else:
            self.write("\n\n\n")

        self.prune()

    n_classdefdeco2 = n_classdef

    def n_const_list(self, node: SyntaxTree):
        """
        prettyprint a constant dict, list, set or tuple.
        """
        p = self.prec

        lastnodetype = node[2].kind
        flat_elems = node[1]
        is_dict = lastnodetype.endswith("DICT")

        if lastnodetype.endswith("LIST"):
            self.write("[")
            endchar = "]"
        elif lastnodetype.endswith("SET") or is_dict:
            self.write("{")
            endchar = "}"
        else:
            # from trepan.api import debug; debug()
            raise TypeError(
                f"Internal Error: n_const_list expects dict, list set, or set; got {lastnodetype}"
            )

        self.indent_more(INDENT_PER_LEVEL)
        sep = ""
        if is_dict:
            keys = flat_elems[-1].attr
            assert isinstance(keys, tuple)
            assert len(keys) == len(flat_elems) - 1

            for i, elem in enumerate(flat_elems[:-1]):
                assert elem.kind == "ADD_VALUE"
                if elem.optype in ("local", "name"):
                    value = elem.attr
                elif elem.optype == "const" and not isinstance(elem.attr, str):
                    value = elem.attr
                else:
                    value = elem.pattr

                if elem.linestart is not None:
                    if elem.linestart != self.line_number:
                        sep += "\n" + self.indent + INDENT_PER_LEVEL[:-1]
                        self.line_number = elem.linestart
                    else:
                        if sep != "":
                            sep += " "
                self.write(f"{sep} {repr(keys[i])}: {value}")
                sep = ","
        else:
            for elem in flat_elems:
                assert elem.kind == "ADD_VALUE"
                if elem.optype in ("local", "name"):
                    value = elem.attr
                elif elem.optype == "const" and not isinstance(elem.attr, str):
                    value = elem.attr
                else:
                    value = elem.pattr

                if elem.linestart is not None:
                    if elem.linestart != self.line_number:
                        sep += "\n" + self.indent + INDENT_PER_LEVEL[:-1]
                        self.line_number = elem.linestart
                    else:
                        if sep != "":
                            sep += " "
                self.write(sep, value)
                sep = ","
        self.write(endchar)
        self.indent_less(INDENT_PER_LEVEL)

        self.prec = p
        self.prune()
        return

    def n_delete_subscript(self, node: SyntaxTree):
        if node[-2][0] == "build_list" and node[-2][0][-1].kind.startswith(
            "BUILD_TUPLE"
        ):
            if node[-2][0][-1] != "BUILD_TUPLE_0":
                node[-2][0].kind = "build_tuple2"
        self.default(node)

    n_store_subscript = n_subscript = n_delete_subscript

    def n_dict(self, node: SyntaxTree):
        """
        Prettyprint a dict.
        'dict' is something like k = {'a': 1, 'b': 42}"
        We will use source-code line breaks to guide us when to break.
        """
        if len(node) == 1 and node[0] == "const_list":
            self.preorder(node[0])
            self.prune()
            return

        p = self.prec
        self.prec = PRECEDENCE["dict"]

        self.indent_more(INDENT_PER_LEVEL)
        sep = INDENT_PER_LEVEL[:-1]
        if node[0] != "dict_entry":
            self.write("{")
        line_number = self.line_number

        if self.version >= (3, 0) and not self.is_pypy:
            if node[0].kind.startswith("kvlist"):
                # Python 3.5+ style key/value list in dict
                kv_node = node[0]
                ll = list(kv_node)
                length = len(ll)
                if kv_node[-1].kind.startswith("BUILD_MAP"):
                    length -= 1
                i = 0

                # Respect line breaks from source
                while i < length:
                    self.write(sep)
                    name = self.traverse(ll[i], indent="")
                    if i > 0:
                        line_number = self.indent_if_source_nl(
                            line_number, self.indent + INDENT_PER_LEVEL[:-1]
                        )
                    line_number = self.line_number
                    self.write(name, ": ")
                    value = self.traverse(
                        ll[i + 1], indent=self.indent + (len(name) + 2) * " "
                    )
                    self.write(value)
                    sep = ", "
                    if line_number != self.line_number:
                        sep += "\n" + self.indent + INDENT_PER_LEVEL[:-1]
                        line_number = self.line_number
                    i += 2
                    pass
                pass
            elif len(node) > 1 and node[1].kind.startswith("kvlist"):
                # Python 3.0..3.4 style key/value list in dict
                kv_node = node[1]
                ll = list(kv_node)
                if len(ll) > 0 and ll[0].kind == "kv3":
                    # Python 3.2 does this
                    kv_node = node[1][0]
                    ll = list(kv_node)
                i = 0
                while i < len(ll):
                    self.write(sep)
                    name = self.traverse(ll[i + 1], indent="")
                    if i > 0:
                        line_number = self.indent_if_source_nl(
                            line_number, self.indent + INDENT_PER_LEVEL[:-1]
                        )
                        pass
                    line_number = self.line_number
                    self.write(name, ": ")
                    value = self.traverse(
                        ll[i], indent=self.indent + (len(name) + 2) * " "
                    )
                    self.write(value)
                    sep = ", "
                    if line_number != self.line_number:
                        sep += "\n" + self.indent + INDENT_PER_LEVEL[:-1]
                        line_number = self.line_number
                    else:
                        sep += " "
                    i += 3
                    pass
                pass
            elif node[-1].kind.startswith("BUILD_CONST_KEY_MAP"):
                # Python 3.6+ style const map
                keys = node[-2].pattr
                values = node[:-2]
                # FIXME: Line numbers?
                for key, value in zip(keys, values):
                    self.write(sep)
                    self.write(repr(key))
                    line_number = self.line_number
                    self.write(":")
                    self.write(self.traverse(value[0]))
                    sep = ", "
                    if line_number != self.line_number:
                        sep += "\n" + self.indent + INDENT_PER_LEVEL[:-1]
                        line_number = self.line_number
                    else:
                        sep += " "
                        pass
                    pass
                if sep.startswith(",\n"):
                    self.write(sep[1:])
                pass
            elif node[0].kind.startswith("dict_entry"):
                assert self.version >= (3, 5)
                template = ("%C", (0, len(node[0]), ", **"))
                self.template_engine(template, node[0])
                sep = ""
            elif node[-1].kind.startswith("BUILD_MAP_UNPACK") or node[
                -1
            ].kind.startswith("dict_entry"):
                assert self.version >= (3, 5)
                # FIXME: I think we can intermingle dict_comp's with other
                # dictionary kinds of things. The most common though is
                # a sequence of dict_comp's
                kwargs = node[-1].attr
                template = ("**%C", (0, kwargs, ", **"))
                self.template_engine(template, node)
                sep = ""

            pass
        elif self.version >= (3, 6) and self.is_pypy:
            # FIXME: DRY with above
            if node[-1].kind.startswith("BUILD_CONST_KEY_MAP"):
                # Python 3.6+ style const map
                keys = node[-2].pattr
                values = node[:-2]
                # FIXME: Line numbers?
                for key, value in zip(keys, values):
                    self.write(sep)
                    self.write(repr(key))
                    line_number = self.line_number
                    self.write(":")
                    self.write(self.traverse(value[0]))
                    sep = ", "
                    if line_number != self.line_number:
                        sep += "\n" + self.indent + INDENT_PER_LEVEL[:-1]
                        line_number = self.line_number
                    else:
                        sep += " "
                        pass
                    pass
                if sep.startswith(",\n"):
                    self.write(sep[1:])
                pass
        else:
            # Python 2 style kvlist. Find beginning of kvlist.
            if node[0].kind.startswith("BUILD_MAP"):
                if len(node) > 1 and node[1].kind in ("kvlist", "kvlist_n"):
                    kv_node = node[1]
                else:
                    kv_node = node[1:]
            else:
                assert node[-1].kind.startswith("kvlist")
                kv_node = node[-1]

            first_time = True
            for kv in kv_node:
                assert kv in ("kv", "kv2", "kv3")

                # kv ::= DUP_TOP expr ROT_TWO expr STORE_SUBSCR
                # kv2 ::= DUP_TOP expr expr ROT_THREE STORE_SUBSCR
                # kv3 ::= expr expr STORE_MAP

                # FIXME: DRY this and the above
                indent = self.indent + "  "
                if kv == "kv":
                    self.write(sep)
                    name = self.traverse(kv[-2], indent="")
                    if first_time:
                        line_number = self.indent_if_source_nl(line_number, indent)
                        first_time = False
                        pass
                    line_number = self.line_number
                    self.write(name, ": ")
                    value = self.traverse(
                        kv[1], indent=self.indent + (len(name) + 2) * " "
                    )
                elif kv == "kv2":
                    self.write(sep)
                    name = self.traverse(kv[1], indent="")
                    if first_time:
                        line_number = self.indent_if_source_nl(line_number, indent)
                        first_time = False
                        pass
                    line_number = self.line_number
                    self.write(name, ": ")
                    value = self.traverse(
                        kv[-3], indent=self.indent + (len(name) + 2) * " "
                    )
                elif kv == "kv3":
                    self.write(sep)
                    name = self.traverse(kv[-2], indent="")
                    if first_time:
                        line_number = self.indent_if_source_nl(line_number, indent)
                        first_time = False
                        pass
                    line_number = self.line_number
                    self.write(name, ": ")
                    line_number = self.line_number
                    value = self.traverse(
                        kv[0], indent=self.indent + (len(name) + 2) * " "
                    )
                    pass
                self.write(value)
                sep = ", "
                if line_number != self.line_number:
                    sep += "\n" + self.indent + INDENT_PER_LEVEL[:-1]
                    line_number = self.line_number
                else:
                    sep += " "
                    pass
                pass
            pass
        if sep.startswith(",\n"):
            self.write(sep[1:])
        if node[0] != "dict_entry":
            self.write("}")
        self.indent_less(INDENT_PER_LEVEL)
        self.prec = p
        self.prune()

    # In the old days this node would never get called because
    # it was embedded inside some sort of comprehension
    # Nowadays, we allow starting any code object, not just
    # a top-level module. In doing so we can
    # now encounter this outside of the embedding of
    # a comprehension.
    def n_dict_comp_func(self, node: SyntaxTree):
        self.write("{")
        self.comprehension_walk_newer(node, 4, 0, collection_node=node[1])
        self.write("}")
        self.prune()

    n_set_comp_func = n_dict_comp_func

    def n_docstring(self, node: SyntaxTree):
        indent = self.indent
        doc_node = node[0]
        if doc_node.attr:
            docstring = doc_node.attr
            if not isinstance(docstring, str):
                # FIXME: we have mistakenly tagged something as a doc
                # string in transform when it isn't one.
                # The rule in n_mkfunc is pretty flaky.
                self.prune()
                return
        else:
            docstring = node[0].pattr

        quote = '"""'
        if docstring.find(quote) >= 0:
            if docstring.find("'''") == -1:
                quote = "'''"

        self.write(indent)
        docstring = repr(docstring.expandtabs())[1:-1]

        for orig, replace in (
            ("\\\\", "\t"),
            ("\\r\\n", "\n"),
            ("\\n", "\n"),
            ("\\r", "\n"),
            ('\\"', '"'),
            ("\\'", "'"),
        ):
            docstring = docstring.replace(orig, replace)

        # Do a raw string if there are backslashes but no other escaped characters:
        # also check some edge cases
        if (
            "\t" in docstring
            and "\\" not in docstring
            and len(docstring) >= 2
            and docstring[-1] != "\t"
            and (docstring[-1] != '"' or docstring[-2] == "\t")
        ):
            self.write("r")  # raw string
            # Restore backslashes unescaped since raw
            docstring = docstring.replace("\t", "\\")
        else:
            # Escape the last character if it is the same as the
            # triple quote character.
            quote1 = quote[-1]
            if len(docstring) and docstring[-1] == quote1:
                docstring = docstring[:-1] + "\\" + quote1

            # Escape triple quote when needed
            if quote == '"""':
                replace_str = '\\"""'
            else:
                assert quote == "'''"
                replace_str = "\\'''"

            docstring = docstring.replace(quote, replace_str)
            docstring = docstring.replace("\t", "\\\\")

        lines = docstring.split("\n")

        self.write(quote)
        if len(lines) == 0:
            self.println(quote)
        elif len(lines) == 1:
            self.println(lines[0], quote)
        else:
            self.println(lines[0])
            for line in lines[1:-1]:
                if line:
                    self.println(line)
                else:
                    self.println("\n\n")
                    pass
                pass
            self.println(lines[-1], quote)
        self.prune()

    def n_elifelsestmtr(self, node: SyntaxTree):
        if node[2] == "COME_FROM":
            return_stmts_node = node[3]
            node.kind = "elifelsestmtr2"
        else:
            return_stmts_node = node[2]

        if len(return_stmts_node) != 2:
            self.default(node)

        for n in return_stmts_node[0]:
            if not (n[0] == "ifstmt" and n[0][1][0] == "return_if_stmts"):
                self.default(node)
                return

        self.write(self.indent, "elif ")
        self.preorder(node[0])
        self.println(":")
        self.indent_more()
        self.preorder(node[1])
        self.indent_less()

        for n in return_stmts_node[0]:
            n[0].kind = "elifstmt"
            self.preorder(n)
        self.println(self.indent, "else:")
        self.indent_more()
        self.preorder(return_stmts_node[1])
        self.indent_less()
        self.prune()

    def n_except_cond2(self, node: SyntaxTree):
        unpack_node = -3 if node[-1] == "come_from_opt" else -2
        if node[unpack_node][0] == "unpack":
            node[unpack_node][0].kind = "unpack_w_parens"
        self.default(node)

    def n_expr(self, node: SyntaxTree):
        first_child = node[0]
        p = self.prec

        if first_child.kind.startswith("bin_op"):
            n = node[0][-1][0]
        else:
            n = node[0]

        # if (hasattr(n, 'linestart') and n.linestart and
        #     hasattr(self, 'current_line_number')):
        #     self.source_linemap[self.current_line_number] = n.linestart

        if n.kind != "expr":
            self.prec = PRECEDENCE.get(n.kind, PARENTHESIS_ALWAYS)

        if n == "LOAD_CONST" and repr(n.pattr)[0] == "-":
            self.prec = 6

        # print("XXX", n.kind, p, "<", self.prec)
        # print(self.f.getvalue())

        if p < self.prec:
            # print(f"PREC {p}, {node[0].kind}")
            self.write("(")
            self.preorder(node[0])
            self.write(")")
        else:
            self.preorder(node[0])
        self.prec = p
        self.prune()

    # In the old days this node would never get called because
    # it was embedded inside some sort of comprehension
    # Nowadays, we allow starting any code object, not just
    # a top-level module. In doing so we can
    # now encounter this outside of the embedding of
    # a comprehension.
    def n_generator_exp(self, node: SyntaxTree):
        self.write("(")
        if node[0].kind in ("load_closure", "load_genexpr") and self.version >= (3, 8):
            is_lambda = self.is_lambda
            self.closure_walk(
                node, collection_index=4 if isinstance(node[4], SyntaxTree) else 3
            )
            self.is_lambda = is_lambda
        else:
            code_index = -6
            if self.version < (3, 8) and node != "genexpr_func":
                iter_index = 4 if node[4] == "expr" else 3
                self.comprehension_walk(node, iter_index=iter_index)
            else:
                self.comprehension_walk_newer(node, iter_index=4, code_index=code_index)
        self.write(")")
        self.prune()

    n_genexpr_func = n_generator_exp_async = n_generator_exp

    def n_ifelsestmtr(self, node):
        if node[2] == "COME_FROM":
            return_stmts_node = node[3]
            node.kind = "ifelsestmtr2"
        else:
            return_stmts_node = node[2]
        if len(return_stmts_node) != 2:
            self.default(node)

        if not (
            return_stmts_node[0][0][0] == "ifstmt"
            and return_stmts_node[0][0][0][1][0] == "return_if_stmts"
        ) and not (
            return_stmts_node[0][-1][0] == "ifstmt"
            and return_stmts_node[0][-1][0][1][0] == "return_if_stmts"
        ):
            self.default(node)
            return

        self.write(self.indent, "if ")
        self.preorder(node[0])
        self.println(":")
        self.indent_more()
        self.preorder(node[1])
        self.indent_less()

        if_ret_at_end = False
        if len(return_stmts_node[0]) >= 3:
            if (
                return_stmts_node[0][-1][0] == "ifstmt"
                and return_stmts_node[0][-1][0][1][0] == "return_if_stmts"
            ):
                if_ret_at_end = True

        past_else = False
        prev_stmt_is_if_ret = True
        for n in return_stmts_node[0]:
            if n[0] == "ifstmt" and n[0][1][0] == "return_if_stmts":
                if prev_stmt_is_if_ret:
                    n[0].kind = "elifstmt"
                prev_stmt_is_if_ret = True
            else:
                prev_stmt_is_if_ret = False
                if not past_else and not if_ret_at_end:
                    self.println(self.indent, "else:")
                    self.indent_more()
                    past_else = True
            self.preorder(n)
        if not past_else or if_ret_at_end:
            self.println(self.indent, "else:")
            self.indent_more()
        self.preorder(return_stmts_node[1])
        self.indent_less()
        self.prune()

    n_ifelsestmtr2 = n_ifelsestmtr

    def n_import_as37(self, node):
        if node[1].attr is not None:
            self.template_engine(
                (
                    "%|from %c import %[1]{attr[0]} as %c\n",
                    (2, ("importlist37", "IMPORT_NAME_ATTR")),
                    (-2, "store"),
                ),
                node,
            )
        else:
            self.template_engine(
                (
                    "%|import %c as %c\n",
                    (2, ("importlist37", "IMPORT_NAME_ATTR")),
                    (-2, "store"),
                ),
                node,
            )
        self.prune()

    def n_lambda_body(self, node: SyntaxTree):
        make_function36(self, node, is_lambda=True, code_node=node[-2])
        self.prune()  # stop recursing

    def n_list(self, node: SyntaxTree):
        """
        prettyprint a dict, list, set or tuple.
        """
        p = self.prec

        if len(node) == 1:
            lastnode = node[0]
            flat_elems = []
        else:
            self.prec = PRECEDENCE["yield"] - 1
            lastnode = node.pop()
            flat_elems = flatten_list(node)

        lastnodetype = lastnode.kind

        if lastnodetype.startswith("BUILD_LIST") or lastnodetype == "expr":
            self.write("[")
            endchar = "]"

        elif lastnodetype.startswith("BUILD_MAP_UNPACK"):
            self.write("{*")
            endchar = "}"

        elif lastnodetype.startswith("BUILD_SET"):
            self.write("{")
            endchar = "}"

        elif lastnodetype.startswith("BUILD_TUPLE") or node == "tuple":
            # Tuples can appear places that can NOT
            # have parenthesis around them, like array
            # subscripts. We check for that by seeing
            # if a tuple item is some sort of slice.
            no_parens = False
            for n in node:
                if n == "arg":
                    n = n[0]
                if n == "expr" and n[0].kind.startswith("slice"):
                    no_parens = True
                    break
                pass
            if no_parens:
                endchar = ""
            else:
                self.write("(")
                endchar = ")"
                pass

        elif lastnodetype.startswith("ROT_TWO"):
            self.write("(")
            endchar = ")"

        else:
            raise TypeError(
                "Internal Error: n_build_list expects list, tuple, set, or unpack"
            )

        self.indent_more(INDENT_PER_LEVEL)
        sep = ""
        for elem in flat_elems:
            if elem in ("ROT_THREE", "EXTENDED_ARG"):
                continue
            assert elem in ("expr", "list", "lists")
            line_number = self.line_number
            value = self.traverse(elem)
            if line_number != self.line_number:
                sep += "\n" + self.indent + INDENT_PER_LEVEL[:-1]
            else:
                if sep != "":
                    sep += " "
            self.write(sep, value)
            sep = ","
        if lastnodetype.startswith("BUILD_TUPLE") and lastnode.attr == 1:
            self.write(",")
        self.write(endchar)
        self.indent_less(INDENT_PER_LEVEL)

        self.prec = p
        self.prune()
        return

    n_set = n_build_set = n_tuple = n_list

    def n_list(self, node):
        """
        prettyprint a dict, list, set or tuple.
        """
        p = self.prec

        if len(node) == 1:
            lastnode = node[0]
            flat_elems = []
        else:
            self.prec = PRECEDENCE["yield"] - 1
            lastnode = node.pop()
            flat_elems = flatten_list(node)

        lastnodetype = lastnode.kind

        if lastnodetype.startswith("BUILD_LIST") or lastnodetype == "expr":
            self.write("[")
            endchar = "]"

        elif lastnodetype.startswith("BUILD_MAP_UNPACK"):
            self.write("{*")
            endchar = "}"

        elif lastnodetype.startswith("BUILD_SET"):
            self.write("{")
            endchar = "}"

        elif lastnodetype.startswith("BUILD_TUPLE") or node == "tuple":
            # Tuples can appear places that can NOT
            # have parenthesis around them, like array
            # subscripts. We check for that by seeing
            # if a tuple item is some sort of slice.
            no_parens = False
            for n in node:
                if n == "arg":
                    n = n[0]
                if n == "expr" and n[0].kind.startswith("slice"):
                    no_parens = True
                    break
                pass
            if no_parens:
                endchar = ""
            else:
                self.write("(")
                endchar = ")"
                pass

        elif lastnodetype.startswith("ROT_TWO"):
            self.write("(")
            endchar = ")"

        else:
            raise TypeError(
                "Internal Error: n_build_list expects list, tuple, set, or unpack"
            )

        self.indent_more(INDENT_PER_LEVEL)
        sep = ""
        for elem in flat_elems:
            if elem in ("ROT_THREE", "EXTENDED_ARG"):
                continue
            assert elem in ("expr", "list", "lists")
            line_number = self.line_number
            value = self.traverse(elem)
            if line_number != self.line_number:
                sep += "\n" + self.indent + INDENT_PER_LEVEL[:-1]
            else:
                if sep != "":
                    sep += " "
            self.write(sep, value)
            sep = ","
        if (
            isinstance(lastnode, Token)
            and lastnode.attr == 1
            and lastnodetype.startswith("BUILD_TUPLE")
        ):
            self.write(",")
        self.write(endchar)
        self.indent_less(INDENT_PER_LEVEL)

        self.prec = p
        self.prune()
        return

    n_set = n_build_set = n_tuple = n_list

    def n_list_comp(self, node):
        self.write("[")
        if node[0].kind == "load_closure":
            self.listcomp_closure3(node)
        else:
            if node == "list_comp_async":
                # comprehension_walk_newer needs to pick out from node since
                # there isn't an iter_index at the top level
                list_iter_index = None
            else:
                list_iter_index = 5 if self.is_pypy else 1
            self.comprehension_walk_newer(node, list_iter_index, 0)
        self.write("]")
        self.prune()

    n_list_comp_async = n_list_comp

    def n_mkfunc(self, node):

        # MAKE_FUNCTION ..
        code_node = node[-3]
        if not iscode(code_node.attr):
            # docstring exists
            code_node = node[-4]

        code = code_node.attr
        assert iscode(code)

        func_name = code.co_name
        self.write(func_name)

        self.indent_more()

        make_function36(self, node, is_lambda=False, code_node=code_node)

        if len(self.param_stack) > 1:
            self.write("\n\n")
        else:
            self.write("\n\n\n")
        self.indent_less()
        self.prune()  # stop recursing

    def n_return(self, node):
        if self.params["is_lambda"] or node[0] in (
            "pop_return",
            "popb_return",
            "pop_ex_return",
        ):
            self.preorder(node[0])
            self.prune()
        else:
            self.write(self.indent, "return")
            # One reason we worry over whether we use "return None" or "return"
            # is that inside a generator, "return None" is illegal.
            # Thank you, Python!
            if self.return_none or not self.is_return_none(node):
                self.write(" ")
                self.preorder(node[0])
            self.println()
            self.prune()  # stop recursing

    def n_return_call_lambda(self, node):

        # Understand where the non-psuedo instructions lie.
        opt_start = 1 if node[0].kind in ("come_from_", "COME_FROM") else 0
        call_index = -3 if node[-1].kind == "COME_FROM" else -2

        call_fn = node[call_index]
        assert call_fn.kind.startswith("CALL_FUNCTION")
        # Just print the args
        self.template_engine(
            ("%P", (opt_start, call_fn.attr + opt_start, ", ", 100)), node
        )
        self.prune()

    def n_return_expr(self, node):
        if len(node) == 1 and node[0] == "expr":
            # If expr is yield we want parens.
            self.prec = PRECEDENCE["yield"] - 1
            self.n_expr(node[0])
        else:
            self.n_expr(node)

    n_return_expr_or_cond = n_expr

    # Python 3.x can have be dead code as a result of its optimization?
    # So we'll add a # at the end of the return lambda so the rest is ignored
    def n_return_expr_lambda(self, node):
        if 1 <= len(node) <= 2:
            self.preorder(node[0])
            self.prune()
        else:
            # We can't comment out dead code like we do above because
            # there may be a trailing ')' that needs to be written.
            assert len(node) == 3 and node[2] in (
                "RETURN_VALUE_LAMBDA",
                "LAMBDA_MARKER",
            )
            self.preorder(node[0])
            self.prune()

    def n_return_if_stmt(self, node):
        if self.params["is_lambda"]:
            self.write(" return ")
            self.preorder(node[0])
            self.prune()
        else:
            self.write(self.indent, "return")
            if self.return_none or not self.is_return_none(node):
                self.write(" ")
                self.preorder(node[0])
            self.println()
            self.prune()  # stop recursing

    def n_set_comp(self, node):
        self.write("{")
        if node[0] in ["LOAD_SETCOMP", "LOAD_DICTCOMP"]:
            self.comprehension_walk_newer(node, 4, 0)
        elif node[0].kind == "load_closure":
            # Token GET_ITER forms or nonterminal "get_iter" forms
            assert node[-2].kind.lower() in ("get_iter", "get_aiter")
            collection_index = -2
            if node[collection_index] == "GET_ITER":
                collection_index -= 1
            self.closure_walk(node, collection_index=collection_index)
        else:
            # Token GET_ITER forms or nonterminal "get_iter" forms
            if node[1] == "set_iter":
                self.comprehension_walk_newer(node[1], iter_index=3)
            else:
                assert node[-2].kind.lower() in ("get_iter", "get_aiter")
                self.comprehension_walk(node, iter_index=-2)
        self.write("}")
        self.prune()

    n_dict_comp = n_set_comp

    # In the old days this node would never get called because
    # it was embedded inside some sort of comprehension
    # Nowadays, we allow starting any code object, not just
    # a top-level module. In doing so we can
    # now encounter this outside of the embedding of
    # a comprehension.
    def n_set_comp_async(self, node):
        self.write("{")
        if node[0] in ["BUILD_SET_0", "BUILD_MAP_0"]:
            self.comprehension_walk_newer(node[1], 3, 0, collection_node=node[1])
        if node[0] in ["LOAD_SETCOMP", "LOAD_DICTCOMP"]:
            get_aiter = node[3]
            assert get_aiter == "get_aiter", node.kind
            self.comprehension_walk_newer(node, 1, 0, collection_node=get_aiter[0])
        self.write("}")
        self.prune()

    n_dict_comp_async = n_set_comp_async

    # This could be a rule but we have handling to remove None
    # e.g. a[:5] rather than a[None:5]
    def n_slice2(self, node):
        p = self.prec
        self.prec = NO_PARENTHESIS_EVER
        if not node[0].isNone():
            self.preorder(node[0])
        self.write(":")
        if not node[1].isNone():
            self.preorder(node[1])
        self.prec = p
        self.prune()  # stop recursing

    # This could be a rule but we have handling to remove None's
    # e.g. a[:] rather than a[None:None]
    def n_slice3(self, node):
        p = self.prec
        self.prec = NO_PARENTHESIS_EVER
        if not node[0].isNone():
            self.preorder(node[0])
        self.write(":")
        if not node[1].isNone():
            self.preorder(node[1])
        self.write(":")
        if not node[2].isNone():
            self.preorder(node[2])
        self.prec = p
        self.prune()  # stop recursing

    def n_str(self, node):
        self.write(node[0].pattr)
        self.prune()

    def n_store(self, node):
        expr = node[0]
        if expr == "expr" and expr[0] == "LOAD_CONST" and node[1] == "STORE_ATTR":
            # FIXME: I didn't record which constants parenthesis is
            # necessary. However, I suspect that we could further
            # refine this by looking at operator precedence and
            # eval'ing the constant value (pattr) and comparing with
            # the type of the constant.
            node.kind = "store_w_parens"
        self.default(node)

    def n_unpack(self, node):
        if node[0].kind.startswith("UNPACK_EX"):
            # Python 3+
            before_count, after_count = node[0].attr
            for i in range(before_count + 1):
                self.preorder(node[i])
                if i != 0:
                    self.write(", ")
            self.write("*")
            for i in range(1, after_count + 2):
                self.preorder(node[before_count + i])
                if i != after_count + 1:
                    self.write(", ")
            self.prune()
            return
        if node[0] == "UNPACK_SEQUENCE_0":
            self.write("[]")
            self.prune()
            return
        for n in node[1:]:
            if n[0].kind == "unpack":
                n[0].kind = "unpack_w_parens"

        unpack_prec = PRECEDENCE["unpack"]
        old_prec = self.prec
        need_parens = old_prec < unpack_prec
        self.prec = unpack_prec
        if need_parens:
            self.write("(")
        try:
            self.default(node)
        except GenericASTTraversalPruningException:
            self.prec = old_prec
            if need_parens:
                self.write(")")
            raise

    n_unpack_w_parens = n_unpack

    def n_yield(self, node):
        if node != SyntaxTree("yield", [NONE, Token("YIELD_VALUE")]):
            self.template_engine(("yield %c", 0), node)
        elif self.version <= (2, 4):
            # Early versions of Python don't allow a plain "yield"
            self.write("yield None")
        else:
            self.write("yield")

        self.prune()  # stop recursing

    def n_LOAD_CONST(self, node):
        attr = node.attr
        data = node.pattr
        datatype = type(data)
        if isinstance(data, float):
            self.write(better_repr(data))
        elif isinstance(data, complex):
            self.write(better_repr(data))
        elif isinstance(datatype, int) and data == minint:
            # convert to hex, since decimal representation
            # would result in 'LOAD_CONST; UNARY_NEGATIVE'
            # change:hG/2002-02-07: this was done for all negative integers
            # todo: check whether this is necessary in Python 2.1
            self.write(hex(data))
        elif datatype is type(Ellipsis):
            self.write("...")
        elif attr is None:
            # LOAD_CONST 'None' only occurs, when None is
            # implicit eg. in 'return' w/o params
            # pass
            self.write("None")
        elif isinstance(data, tuple):
            self.pp_tuple(data)
        elif isinstance(attr, bool):
            self.write(repr(attr))
        elif self.FUTURE_UNICODE_LITERALS:
            # The FUTURE_UNICODE_LITERALS compiler flag
            # in 2.6 on change the way
            # strings are interpreted:
            #    u'xxx' -> 'xxx'
            #    xxx'   -> b'xxx'
            if isinstance(data, str):
                self.write("b" + repr(data))
            else:
                self.write(repr(data))
        else:
            self.write(repr(data))
        # LOAD_CONST is a terminal, so stop processing/recursing early
        self.prune()
