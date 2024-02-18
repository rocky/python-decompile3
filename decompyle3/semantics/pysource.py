#  Copyright (c) 2015-2024 by Rocky Bernstein
#  Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
#  Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
#  Copyright (c) 1999 John Aycock
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

"""Creates Python source code from an decompyle3 parse tree.

The terminal symbols are CPython bytecode instructions. (See the
python documentation under module "dis" for a list of instructions
and what they mean).

Upper levels of the grammar is a more-or-less conventional grammar for
Python.
"""

# The below is a bit long, but still it is somewhat abbreviated.
# See https://github.com/rocky/python-uncompyle6/wiki/Table-driven-semantic-actions.
# for a more complete explanation, nicely marked up and with examples.
#
#
# Semantic action rules for nonterminal symbols can be specified here by
# creating a method prefaced with "n_" for that nonterminal. For
# example, "n_exec_stmt" handles the semantic actions for the
# "exec_stmt" nonterminal symbol. Similarly if a method with the name
# of the nonterminal is suffixed with "_exit" it will be called after
# all of its children are called.
#
# After a while writing methods this way, you'll find many routines which do similar
# sorts of things, and soon you'll find you want a short notation to
# describe rules and not have to create methods at all.
#
# So another other way to specify a semantic rule for a nonterminal is via
# either tables MAP_R, or MAP_DIRECT where the key is the
# nonterminal name.
#
# These dictionaries use a printf-like syntax to direct substitution
# from attributes of the nonterminal and its children..
#
# The rest of the below describes how table-driven semantic actions work
# and gives a list of the format specifiers. The default() and
# template_engine() methods implement most of the below.
#
# We allow for a couple of ways to interact with a node in a tree.  So
# step 1 after not seeing a custom method for a nonterminal is to
# determine from what point of view tree-wise the rule is applied.

# In the diagram below, N is a nonterminal name, and K also a nonterminal
# name but the one used as a key in the table.
# we show where those are with respect to each other in the
# parse tree for N.
#
#
#          N&K               N
#         / | ... \        / | ... \
#        O  O      O      O  O      K
#
#
#      TABLE_DIRECT      TABLE_R
#
#   The default table is TABLE_DIRECT mapping By far, most rules used work this way.
#
#   The key K is then extracted from the subtree and used to find one
#   of the tables, T listed above.  The result after applying T[K] is
#   a format string and arguments (a la printf()) for the formatting
#   engine.
#
#   Escapes in the format string are:
#
#     %c  evaluate/traverse the node recursively. Its argument is a single
#         integer or tuple representing a node index.
#         If a tuple is given, the first item is the node index while
#         the second item is a string giving the node/noterminal name.
#         This name will be checked at runtime against the node type.
#
#     %p  like %c but sets the operator precedence.
#         Its argument then is a tuple indicating the node
#         index and the precedence value, an integer. If 3 items are given,
#         the second item is the nonterminal name and the precedence is given last.
#
#     %C  evaluate/travers children recursively, with sibling children separated by the
#         given string.  It needs a 3-tuple: a starting node, the maximum
#         value of an end node, and a string to be inserted between sibling children
#
#     %,  Append ',' if last %C only printed one item. This is mostly for tuples
#         on the LHS of an assignment statement since BUILD_TUPLE_n pretty-prints
#         other tuples. The specifier takes no arguments
#
#     %P  same as %C but sets operator precedence.  Its argument is a 4-tuple:
#         the node low and high indices, the separator, a string the precedence
#         value, an integer.
#
#     %D Same as `%C` this is for left-recursive lists like kwargs where goes
#         to epsilon at the beginning. It needs a 3-tuple: a starting node, the
#         maximum value of an end node, and a string to be inserted between
#         sibling children. If we were to use `%C` an extra separator with an
#         epsilon would appear at the beginning.
#
#     %|  Insert spaces to the current indentation level. Takes no arguments.
#
#     %+ increase current indentation level. Takes no arguments.
#
#     %- decrease current indentation level. Takes no arguments.
#
#     %{EXPR} Python eval(EXPR) in context of node. Takes no arguments
#
#     %[N]{EXPR} Python eval(EXPR) in context of node[N]. Takes no arguments
#
#     %[N]{%X} evaluate/recurse on child node[N], using specifier %X.
#     %X can be one of the above, e.g. %c, %p, etc. Takes the arguments
#     that the specifier uses.
#
#     %% literal '%'. Takes no arguments.
#
#
#   The '%' may optionally be followed by a number (C) in square
#   brackets, which makes the template_engine walk down to N[C] before
#   evaluating the escape code.

import sys
from io import StringIO
from typing import Optional

from spark_parser import GenericASTTraversal
from xdis import COMPILER_FLAG_BIT, IS_PYPY, iscode
from xdis.version_info import PYTHON_VERSION_TRIPLE

import decompyle3.parsers.main as python_parser
import decompyle3.parsers.parse_heads as heads
from decompyle3.parsers.main import get_python_parser
from decompyle3.parsers.treenode import SyntaxTree
from decompyle3.scanner import Code, get_scanner
from decompyle3.scanners.tok import Token
from decompyle3.semantics.check_ast import checker
from decompyle3.semantics.consts import (
    INDENT_PER_LEVEL,
    LINE_LENGTH,
    MAP,
    MAP_DIRECT,
    NAME_MODULE,
    NO_PARENTHESIS_EVER,
    NONE,
    PASS,
    PRECEDENCE,
    TAB,
    TABLE_R,
    escape,
)
from decompyle3.semantics.customize import customize_for_version
from decompyle3.semantics.gencomp import ComprehensionMixin
from decompyle3.semantics.helper import find_globals_and_nonlocals, is_lambda_mode
from decompyle3.semantics.n_actions import NonterminalActions
from decompyle3.semantics.parser_error import ParserError
from decompyle3.semantics.transform import TreeTransform
from decompyle3.show import maybe_show_tree
from decompyle3.util import better_repr

PARSER_DEFAULT_DEBUG = {
    "rules": False,
    "transition": False,
    "reduce": False,
    "errorstack": "full",
    "context": True,
    "dups": False,
}

TREE_DEFAULT_DEBUG = {"before": False, "after": False}

DEFAULT_DEBUG_OPTS = {
    "asm": False,
    "tree": TREE_DEFAULT_DEBUG,
    "grammar": dict(PARSER_DEFAULT_DEBUG),
}


class SourceWalkerError(Exception):
    def __init__(self, errmsg):
        self.errmsg = errmsg

    def __str__(self):
        return self.errmsg


class SourceWalker(GenericASTTraversal, NonterminalActions, ComprehensionMixin):
    """
    Class to traverse a Parse Tree of the bytecode instruction built from parsing to
    produce some sort of source text.
    The Parse tree may be turned an Abstract Syntax tree as an intermediate step.
    """

    stacked_params = ("f", "indent", "is_lambda", "_globals")

    def __init__(
        self,
        version: tuple,
        out,
        scanner,
        showast=TREE_DEFAULT_DEBUG,
        debug_parser=PARSER_DEFAULT_DEBUG,
        compile_mode="exec",
        is_pypy=IS_PYPY,
        linestarts={},
        tolerate_errors=False,
    ):
        """`version' is the Python version of the Python dialect
        of both the syntax tree and language we should produce.

        `out' is IO-like file pointer to where the output should go. It
        would have a getvalue() method.

        `scanner' is a method to call when we need to scan tokens. Sometimes
        in producing output we will run across further tokens that need
        to be scanned.

        If `showast' is True, we print the syntax tree.

        `compile_mode` is is either `exec`, `single` or `lambda`.

        For `lambda`, the grammar that can be used in lambda
        expressions is used.  Otherwise, it is the compile mode that
        was used to create the Syntax Tree and specifies a grammar
        variant within a Python version to use.

        `is_pypy` should be True if the Syntax Tree was generated for PyPy.

        `linestarts` is a dictionary of line number to bytecode offset. This
        can sometimes assist in determining which kind of source-code construct
        to use when there is ambiguity.

        """
        GenericASTTraversal.__init__(self, ast=None)

        self.scanner = scanner
        params = {"f": out, "indent": ""}
        self.version = version
        self.p = get_python_parser(
            version,
            debug_parser=dict(debug_parser),
            compile_mode=compile_mode,
            is_pypy=is_pypy,
        )

        # Initialize p_lambda on demand
        self.p_lambda = None

        self.treeTransform = TreeTransform(
            version=self.version,
            show_ast=showast,
            str_with_template=self.str_with_template,
        )

        # FIXME: have p.insts update in a better way
        # modularity is broken here
        self.p.insts = scanner.insts

        self.ERROR = None
        self.ast_errors = []
        self.classes = []
        self.compile_mode = compile_mode
        self.currentclass = None
        self.debug_parser = dict(debug_parser)
        self.is_module = False
        self.is_pypy = is_pypy
        self.line_number = 1
        self.linestarts = linestarts
        self.mod_globs = set()
        self.name = None
        self.offset2inst_index = scanner.offset2inst_index
        self.param_stack = []
        self.params = params
        self.pending_newlines = 0
        self.prec = NO_PARENTHESIS_EVER
        self.return_none = False
        self.showast = showast
        self.source_linemap = {}
        self.version = version

        # This is in Python 2.6 on. It changes the way
        # strings get interpreted. See n_LOAD_CONST
        self.FUTURE_UNICODE_LITERALS = False

        # Sometimes we may want to continue decompiling when there are errors
        # and sometimes not
        self.tolerate_errors = tolerate_errors

        # If we are in a 3.6+ format string, we may need an
        # extra level of parens when seeing a lambda. We also use
        # this to understand whether or not to add the "f" prefix.
        # When not "None" it is a string of the last nonterminal
        # that started the format string
        self.in_format_string = None

        # hide_internal suppresses displaying the additional instructions that sometimes
        # exist in code but were not written in the source code.
        # An example is:
        # __module__ = __name__
        self.hide_internal = True
        customize_for_version(self, is_pypy, version)
        return

    def maybe_show_tree(self, tree, phase):
        phase_name = "parse_tree" if phase == "before" else "transformed_tree"
        if self.showast.get(phase, False):
            self.println(f"""\n# ---- {phase_name}:\n""" + " ")
            maybe_show_tree(self, tree)

    def str_with_template(self, tree):
        stream = sys.stdout
        stream.write(self.str_with_template1(tree, "", None))
        stream.write("\n")

    def str_with_template1(self, tree, indent: str, sibNum=None) -> str:
        rv = str(tree.kind)

        if sibNum is not None:
            rv = "%2d. %s" % (sibNum, rv)
        enumerate_children = False
        if len(tree) > 1:
            rv += f" ({len(tree)})"
            enumerate_children = True

        if tree in PRECEDENCE:
            rv += f", precedence {PRECEDENCE[tree]}"

        mapping = self._get_mapping(tree)
        table = mapping[0]
        key = tree
        for i in mapping[1:]:
            key = key[i]
            pass

        if tree.transformed_by is not None:
            if tree.transformed_by:
                rv += f" (transformed by {tree.transformed_by})"
            pass
        if key.kind in table:
            rv += ": %s" % str(table[key.kind])

        rv = indent + rv
        indent += "    "
        i = 0
        for node in tree:
            if hasattr(node, "__repr1__"):
                if enumerate_children:
                    child = self.str_with_template1(node, indent, i)
                else:
                    child = self.str_with_template1(node, indent, None)
            else:
                inst = node.format(line_prefix="L.")
                if inst.startswith("\n"):
                    # Nuke leading \n
                    inst = inst[1:]
                if enumerate_children:
                    child = indent + "%2d. %s" % (i, inst)
                else:
                    child = indent + inst
                pass
            rv += "\n" + child
            i += 1
        return rv

    def indent_if_source_nl(self, line_number: int, indent_spaces: str):
        if line_number != self.line_number:
            self.write("\n" + indent_spaces + INDENT_PER_LEVEL[:-1])
        return self.line_number

    f = property(
        lambda s: s.params["f"],
        lambda s, x: s.params.__setitem__("f", x),
        lambda s: s.params.__delitem__("f"),
        None,
    )

    indent = property(
        lambda s: s.params["indent"],
        lambda s, x: s.params.__setitem__("indent", x),
        lambda s: s.params.__delitem__("indent"),
        None,
    )

    is_lambda = property(
        lambda s: s.params["is_lambda"],
        lambda s, x: s.params.__setitem__("is_lambda", x),
        lambda s: s.params.__delitem__("is_lambda"),
        None,
    )

    _globals = property(
        lambda s: s.params["_globals"],
        lambda s, x: s.params.__setitem__("_globals", x),
        lambda s: s.params.__delitem__("_globals"),
        None,
    )

    def set_pos_info(self, node):
        if hasattr(node, "linestart") and node.linestart:
            self.line_number = node.linestart

    def preorder(self, node=None):
        super(SourceWalker, self).preorder(node)
        self.set_pos_info(node)

    def indent_more(self, indent=TAB):
        self.indent += indent

    def indent_less(self, indent=TAB):
        self.indent = self.indent[: -len(indent)]

    def traverse(self, node, indent=None, is_lambda=False):
        self.param_stack.append(self.params)
        if indent is None:
            indent = self.indent
        p = self.pending_newlines
        self.pending_newlines = 0
        self.params = {
            "_globals": {},
            "_nonlocals": {},  # Python 3 has nonlocal
            "f": StringIO(),
            "indent": indent,
            "is_lambda": is_lambda,
        }
        self.preorder(node)
        self.f.write("\n" * self.pending_newlines)
        result = self.f.getvalue()
        self.params = self.param_stack.pop()
        self.pending_newlines = p
        return result

    def write(self, *data):
        if (len(data) == 0) or (len(data) == 1 and data[0] == ""):
            return
        out = "".join((str(j) for j in data))
        n = 0
        for i in out:
            if i == "\n":
                n += 1
                if n == len(out):
                    self.pending_newlines = max(self.pending_newlines, n)
                    return
            elif n:
                self.pending_newlines = max(self.pending_newlines, n)
                out = out[n:]
                break
            else:
                break

        if self.pending_newlines > 0:
            self.f.write("\n" * self.pending_newlines)
            self.pending_newlines = 0

        for i in out[::-1]:
            if i == "\n":
                self.pending_newlines += 1
            else:
                break

        if self.pending_newlines:
            out = out[: -self.pending_newlines]
        self.f.write(out)

    def println(self, *data):
        if data and not (len(data) == 1 and data[0] == ""):
            self.write(*data)
        self.pending_newlines = max(self.pending_newlines, 1)

    def is_return_none(self, node):
        # Is there a better way?
        ret = (
            node[0] == "return_expr"
            and node[0][0] == "expr"
            and node[0][0][0] == "LOAD_CONST"
            and node[0][0][0].pattr is None
        )

        # FIXME: should the SyntaxTree expression be folded into
        # the global RETURN_NONE constant?
        return ret or node == SyntaxTree(
            "return", [SyntaxTree("return_expr", [NONE]), Token("RETURN_VALUE")]
        )

    def pp_tuple(self, tup):
        """Pretty print a tuple"""
        last_line = self.f.getvalue().split("\n")[-1]
        ll = len(last_line) + 1
        indent = " " * ll
        self.write("(")
        sep = ""
        for item in tup:
            self.write(sep)
            ll += len(sep)
            s = better_repr(item)
            ll += len(s)
            self.write(s)
            sep = ","
            if ll > LINE_LENGTH:
                ll = 0
                sep += "\n" + indent
            else:
                sep += " "
                pass
            pass
        if len(tup) == 1:
            self.write(", ")
        self.write(")")

    def print_super_classes(self, node):
        if not (node == "tuple"):
            return

        n_subclasses = len(node[:-1])
        if n_subclasses > 0 or self.version > (2, 4):
            # Not an old-style pre-2.2 class
            self.write("(")

        line_separator = ", "
        sep = ""
        for elem in node[:-1]:
            value = self.traverse(elem)
            self.write(sep, value)
            sep = line_separator

        if n_subclasses > 0 or self.version > (2, 4):
            # Not an old-style pre-2.2 class
            self.write(")")

    def print_super_classes3(self, node):
        n = len(node) - 1
        j = 0
        if node.kind != "expr":
            if node == "kwarg":
                self.template_engine(("(%[0]{attr}=%c)", 1), node)
                return

            kwargs = None
            opname = node[n].kind
            assert opname.startswith("CALL_FUNCTION") or opname.startswith(
                "CALL_METHOD"
            )

            if node[n].kind.startswith("CALL_FUNCTION_KW"):
                # 3.6+ starts doing this
                kwargs = node[n - 1].attr
                assert isinstance(kwargs, tuple)
                i = n - (len(kwargs) + 1)
                j = 1 + n - node[n].attr
            else:
                i = start = n - 2
                for i in range(start, 0, -1):
                    if not node[i].kind in ["expr", "call", "LOAD_CLASSNAME"]:
                        break
                    pass

                if i == start:
                    return
                i += 2

            line_separator = ", "
            sep = ""
            self.write("(")
            if kwargs:
                # Last arg is tuple of keyword values: omit
                m = n - 1
            else:
                m = n

            if kwargs:
                # 3.6+ does this
                while j < i:
                    self.write(sep)
                    value = self.traverse(node[j])
                    self.write("%s" % value)
                    sep = line_separator
                    j += 1

                j = 0
                while i < m:
                    self.write(sep)
                    value = self.traverse(node[i])
                    self.write("%s=%s" % (kwargs[j], value))
                    sep = line_separator
                    j += 1
                    i += 1
            else:
                while i < m:
                    value = self.traverse(node[i])
                    i += 1
                    self.write(sep, value)
                    sep = line_separator
                    pass
            pass
        elif node == "dict_comp_async":
            # Handled this condition above.
            pass
        else:
            if node[0] == "LOAD_STR":
                return
            value = self.traverse(node[0])
            self.write("(")
            self.write(value)
            pass

        self.write(")")

    def template_engine(self, entry, startnode):
        """The format template interpretation engine.  See the comment at the
        beginning of this module for how we interpret format
        specifications such as %c, %C, and so on.
        """

        # print("-----")
        # print(startnode.kind)
        # print(entry[0])
        # print('======')

        fmt = entry[0]
        arg = 1
        i = 0

        m = escape.search(fmt)
        while m:
            i = m.end()
            self.write(m.group("prefix"))

            typ = m.group("type") or "{"
            node = startnode
            if m.group("child"):
                node = node[int(m.group("child"))]

            if typ == "%":
                self.write("%")
            elif typ == "+":
                self.line_number += 1
                self.indent_more()
            elif typ == "-":
                self.line_number += 1
                self.indent_less()
            elif typ == "|":
                self.line_number += 1
                self.write(self.indent)
            # Used mostly on the LHS of an assignment
            # BUILD_TUPLE_n is pretty printed and may take care of other uses.
            elif typ == ",":
                if node.kind in ("unpack", "unpack_w_parens") and node[0].attr == 1:
                    self.write(",")
            elif typ == "c":
                index = entry[arg]
                if isinstance(index, tuple):
                    if isinstance(index[1], str):
                        assert (
                            node[index[0]] == index[1]
                        ), "at %s[%d], expected '%s' node; got '%s'" % (
                            node.kind,
                            arg,
                            index[1],
                            node[index[0]].kind,
                        )
                    else:
                        assert (
                            node[index[0]] in index[1]
                        ), "at %s[%d], expected to be in '%s' node; got '%s'" % (
                            node.kind,
                            arg,
                            index[1],
                            node[index[0]].kind,
                        )

                    index = index[0]
                assert isinstance(
                    index, int
                ), "at %s[%d], %s should be int or tuple" % (
                    node.kind,
                    arg,
                    type(index),
                )

                try:
                    node[index]
                except IndexError:
                    raise RuntimeError(
                        f"""
                        Expanding '{node.kind}' in template '{entry}[{arg}]':
                        {index} is invalid; has only {len(node)} entries
                        """
                    )
                self.preorder(node[index])

                arg += 1
            elif typ == "p":
                p = self.prec
                # entry[arg]
                tup = entry[arg]
                assert isinstance(tup, tuple)
                if len(tup) == 3:
                    (index, nonterm_name, self.prec) = tup
                    if isinstance(tup[1], str):
                        assert (
                            node[index] == nonterm_name
                        ), "at %s[%d], expected '%s' node; got '%s'" % (
                            node.kind,
                            arg,
                            nonterm_name,
                            node[index].kind,
                        )
                    else:
                        assert node[tup[0]] in tup[1], (
                            f"at {node.kind}[{tup[0]}], expected to be in '{tup[1]}' "
                            f"node; got '{node[tup[0]].kind}'"
                        )

                else:
                    assert len(tup) == 2
                    (index, self.prec) = entry[arg]

                self.preorder(node[index])
                self.prec = p
                arg += 1
            elif typ == "C":
                low, high, sep = entry[arg]
                remaining = len(node[low:high])
                for subnode in node[low:high]:
                    self.preorder(subnode)
                    remaining -= 1
                    if remaining > 0:
                        self.write(sep)
                        pass
                    pass
                arg += 1
            elif typ == "D":
                low, high, sep = entry[arg]
                remaining = len(node[low:high])
                for subnode in node[low:high]:
                    remaining -= 1
                    if len(subnode) > 0:
                        self.preorder(subnode)
                        if remaining > 0:
                            self.write(sep)
                            pass
                        pass
                    pass
                arg += 1
            elif typ == "x":
                # This code is only used in fragments
                assert isinstance(entry[arg], tuple)
                arg += 1
            elif typ == "P":
                p = self.prec
                low, high, sep, self.prec = entry[arg]
                remaining = len(node[low:high])
                # remaining = len(node[low:high])
                for subnode in node[low:high]:
                    self.preorder(subnode)
                    remaining -= 1
                    if remaining > 0:
                        self.write(sep)
                self.prec = p
                arg += 1
            elif typ == "{":
                expr = m.group("expr")

                # Line mapping stuff
                if (
                    hasattr(node, "linestart")
                    and node.linestart
                    and hasattr(node, "current_line_number")
                ):
                    self.source_linemap[self.current_line_number] = node.linestart

                if expr[0] == "%":
                    index = entry[arg]
                    self.template_engine((expr, index), node)
                    arg += 1
                else:
                    d = node.__dict__
                    try:
                        self.write(eval(expr, d, d))
                    except Exception:
                        raise
            m = escape.search(fmt, i)
        self.write(fmt[i:])

    def default(self, node):
        mapping = self._get_mapping(node)
        table = mapping[0]
        key = node

        for i in mapping[1:]:
            key = key[i]
            pass

        if key.kind in table:
            self.template_engine(table[key.kind], node)
            self.prune()

    def customize(self, customize):
        """
        Special handling for opcodes, such as those that take a variable number
        of arguments -- we add a new entry for each in TABLE_R.
        """
        for k, v in list(customize.items()):
            if k in TABLE_R:
                continue
            op = k[: k.rfind("_")]

            if k.startswith("CALL_METHOD"):
                # This happens in PyPy and Python 3.7+
                TABLE_R[k] = ("%c(%P)", 0, (1, -1, ", ", 100))
            elif k.startswith("CALL_FUNCTION_KW"):
                TABLE_R[k] = ("%c(%P)", 0, (1, -1, ", ", 100))
            elif op == "CALL_FUNCTION":
                TABLE_R[k] = (
                    "%c(%P)",
                    (0, "expr"),
                    (1, -1, ", ", PRECEDENCE["yield"] - 1),
                )
            elif op in (
                "CALL_FUNCTION_VAR",
                "CALL_FUNCTION_VAR_KW",
                "CALL_FUNCTION_KW",
            ):
                # FIXME: handle everything in customize.
                # Right now, some of this is here, and some in that.

                if v == 0:
                    template_str = "%c(%C"  # '%C' is a dummy here ...
                    p2 = (0, 0, None)  # because of the None in this
                else:
                    template_str = "%c(%C, "
                    p2 = (1, -2, ", ")
                if op == "CALL_FUNCTION_VAR":
                    # Python 3.5 only puts optional args (the VAR part)
                    # the lowest down the stack
                    if self.version == (3, 5):
                        if template_str == "%c(%C, ":
                            entry = ("%c(*%C, %c)", 0, p2, -2)
                        elif template_str == "%c(%C":
                            entry = ("%c(*%C)", 0, (1, 100, ""))
                    elif self.version == (3, 4):
                        # CALL_FUNCTION_VAR's top element of the stack contains
                        # the variable argument list
                        if v == 0:
                            template_str = "%c(*%c)"
                            entry = (template_str, 0, -2)
                        else:
                            template_str = "%c(%C, *%c)"
                            entry = (template_str, 0, p2, -2)
                    else:
                        template_str += "*%c)"
                        entry = (template_str, 0, p2, -2)
                elif op == "CALL_FUNCTION_KW":
                    template_str += "**%c)"
                    entry = (template_str, 0, p2, -2)
                elif op == "CALL_FUNCTION_VAR_KW":
                    template_str += "*%c, **%c)"
                    # Python 3.5 only puts optional args (the VAR part)
                    # the lowest down the stack
                    na = v & 0xFF  # positional parameters
                    if self.version == (3, 5) and na == 0:
                        if p2[2]:
                            p2 = (2, -2, ", ")
                        entry = (template_str, 0, p2, 1, -2)
                    else:
                        if p2[2]:
                            p2 = (1, -3, ", ")
                        entry = (template_str, 0, p2, -3, -2)
                    pass
                else:
                    assert False, "Unhandled CALL_FUNCTION %s" % op

                TABLE_R[k] = entry
                pass
            # handled by n_dict:
            # if op == 'BUILD_SLICE':	TABLE_R[k] = ('%C'    ,    (0,-1,':'))
            # handled by n_list:
            # if   op == 'BUILD_LIST':	TABLE_R[k] = ('[%C]'  ,    (0,-1,', '))
            # elif op == 'BUILD_TUPLE':	TABLE_R[k] = ('(%C%,)',    (0,-1,', '))
            pass
        return

    def build_class(self, code):
        """Dump class definition, doc string and class body."""

        assert iscode(code)
        self.classes.append(self.currentclass)
        code = Code(code, self.scanner, self.currentclass)

        indent = self.indent
        # self.println(indent, '#flags:\t', int(code.co_flags))
        tree = self.build_ast(code._tokens, code._customize, code)

        # save memory by deleting no-longer-used structures
        code._tokens = None

        assert tree == "stmts"

        if tree[0] == "docstring":
            self.println(self.traverse(tree[0]))
            del tree[0]

        first_stmt = tree[0]
        try:
            if first_stmt == NAME_MODULE:
                if self.hide_internal:
                    del tree[0]
                    first_stmt = tree[0]
            pass
        except Exception:
            pass

        have_qualname = False

        # Python 3.4+ has constants like 'cmp_to_key.<locals>.K'
        # which are not simple classes like the < 3 case.

        try:
            if (
                first_stmt == "assign"
                and first_stmt[0][0] == "LOAD_STR"
                and first_stmt[1] == "store"
                and first_stmt[1][0] == Token("STORE_NAME", pattr="__qualname__")
            ):
                have_qualname = True
        except Exception:
            pass

        if have_qualname:
            if self.hide_internal:
                del tree[0]
            pass

        globals, nonlocals = find_globals_and_nonlocals(
            tree, set(), set(), code, self.version
        )
        # Add "global" declaration statements at the top
        # of the function
        for g in sorted(globals):
            self.println(indent, "global ", g)

        for nl in sorted(nonlocals):
            self.println(indent, "nonlocal ", nl)

        old_name = self.name
        self.gen_source(tree, code.co_name, code._customize)
        self.name = old_name

        # save memory by deleting no-longer-used structures
        code._tokens = None
        code._customize = None

        self.classes.pop(-1)

    def gen_source(
        self,
        tree,
        name,
        customize,
        is_lambda=False,
        returnNone=False,
        debug_opts=DEFAULT_DEBUG_OPTS,
    ):
        """convert parse tree to Python source code"""

        rn = self.return_none
        self.return_none = returnNone
        old_name = self.name
        self.name = name
        self.debug_opts = debug_opts
        # if code would be empty, append 'pass'
        if len(tree) == 0:
            self.println(self.indent, "pass")
        else:
            self.customize(customize)
            self.text = self.traverse(tree, is_lambda=is_lambda)
            # In a formatted string using "lambda',  we should not add "\n".
            # For example in:
            #    f'{(lambda x:x)("8")!r}'
            # Adding a "\n" after "lambda x: x" will give an error message:
            #    SyntaxError: f-string expression part cannot include a backslash
            # So avoid that.
            printfn = (
                self.write if (self.in_format_string or is_lambda) else self.println
            )
            printfn(self.text)
        self.name = old_name
        self.return_none = rn

    def build_ast(
        self,
        tokens,
        customize,
        code,
        is_lambda=False,
        noneInNames=False,
        is_top_level_module=False,
    ) -> GenericASTTraversal:
        # FIXME: DRY with fragments.py

        # assert isinstance(tokens[0], Token)

        if is_lambda:
            for t in tokens:
                if t.kind == "RETURN_END_IF":
                    t.kind = "RETURN_END_IF_LAMBDA"
                elif t.kind == "RETURN_VALUE":
                    t.kind = "RETURN_VALUE_LAMBDA"
            tokens.append(Token("LAMBDA_MARKER", optype="pseudo"))
            try:
                if self.p_lambda is None:
                    self.p_lambda = get_python_parser(
                        self.version,
                        self.debug_parser,
                        compile_mode="lambda",
                        is_pypy=self.is_pypy,
                    )
                p = self.p_lambda
                p.insts = self.scanner.insts
                p.offset2inst_index = self.scanner.offset2inst_index
                parse_tree = python_parser.parse(p, tokens, customize, is_lambda)
                self.customize(customize)

            except (heads.ParserError, AssertionError) as e:
                raise ParserError(e, tokens, self.p.debug["reduce"])

            transform_tree = self.treeTransform.transform(
                parse_tree, code, self.println
            )

            del parse_tree  # Save memory
            return transform_tree

        # The bytecode for the end of the main routine has a "return
        # None". However, you can't issue a "return" statement in
        # main. So as the old cigarette slogan goes: I'd rather switch
        # (the token stream) than fight (with the grammar to not emit
        # "return None").
        if self.hide_internal:
            if len(tokens) >= 2 and not noneInNames:
                if tokens[-1].kind in ("RETURN_VALUE", "RETURN_VALUE_LAMBDA"):
                    # Python 3.4's classes can add a "return None" which is
                    # invalid syntax.
                    load_const = tokens[-2]
                    if load_const.kind == "LOAD_CONST":
                        if is_top_level_module or load_const.pattr is None:
                            del tokens[-2:]
                        else:
                            tokens.append(Token("RETURN_LAST"))
                    else:
                        tokens.append(Token("RETURN_LAST"))
            if len(tokens) == 0:
                return PASS

        # Build a parse tree from a tokenized and massaged disassembly.
        try:
            # FIXME: have p.insts update in a better way
            # Modularity is broken here.
            p_insts = self.p.insts
            self.p.insts = self.scanner.insts
            self.p.offset2inst_index = self.scanner.offset2inst_index
            self.p.opc = self.scanner.opc
            parse_tree = python_parser.parse(
                self.p, tokens, customize, is_lambda=is_lambda
            )

            self.p.insts = p_insts
        except (ParserError, AssertionError) as e:
            raise ParserError(e, tokens, self.p.debug["reduce"])

        checker(parse_tree, False, self.ast_errors)

        self.customize(customize)

        transform_tree = self.treeTransform.transform(parse_tree, code, self.println)

        del parse_tree  # Save memory
        return transform_tree

    @classmethod
    def _get_mapping(cls, node):
        return MAP.get(node, MAP_DIRECT)


def code_deparse(
    co,
    out=sys.stdout,
    version: Optional[tuple] = None,
    debug_opts=DEFAULT_DEBUG_OPTS,
    code_objects={},
    compile_mode="exec",
    is_pypy=IS_PYPY,
    walker=SourceWalker,
    start_offset: int = 0,
    stop_offset: int = -1,
) -> Optional[SourceWalker]:
    """
    ingests and deparses a given code block 'co'. If version is None,
    we will use the current Python interpreter version.
    """

    assert iscode(co)

    if out is None:
        out = sys.stdout

    if version is None:
        version = PYTHON_VERSION_TRIPLE

    # store final output stream for case of error
    scanner = get_scanner(version, is_pypy=is_pypy, show_asm=debug_opts["asm"])

    tokens, customize = scanner.ingest(
        co, code_objects=code_objects, show_asm=debug_opts["asm"]
    )

    if start_offset > 0:
        for i, t in enumerate(tokens):
            # If t.offset is a string, we want to skip this.
            if isinstance(t.offset, int) and t.offset >= start_offset:
                tokens = tokens[i:]
                break

    if stop_offset > -1:
        for i, t in enumerate(tokens):
            # In contrast to the test for start_offset If t.offset is
            # a string, we want to extract the integer offset value.
            if t.off2int() >= stop_offset:
                tokens = tokens[:i]
                break

    debug_parser = debug_opts.get("grammar", dict(PARSER_DEFAULT_DEBUG))

    #  Build Syntax Tree from disassembly.
    linestarts = dict(scanner.opc.findlinestarts(co))
    deparsed = walker(
        version,
        out,
        scanner,
        showast=debug_opts.get("tree", TREE_DEFAULT_DEBUG),
        debug_parser=debug_parser,
        compile_mode=compile_mode,
        is_pypy=is_pypy,
        linestarts=linestarts,
    )

    is_top_level_module = co.co_name == "<module>"
    if compile_mode == "eval":
        deparsed.hide_internal = False
    deparsed.compile_mode = compile_mode
    deparsed.ast = deparsed.build_ast(
        tokens,
        customize,
        co,
        is_lambda=is_lambda_mode(compile_mode),
        is_top_level_module=is_top_level_module,
    )

    # XXX workaround for profiling
    if deparsed.ast is None:
        return None

    # FIXME use a lookup table here.
    if is_lambda_mode(compile_mode):
        expected_start = "lambda_start"
    elif compile_mode == "eval":
        expected_start = "expr_start"
    elif compile_mode == "expr":
        expected_start = "expr_start"
    elif compile_mode == "exec":
        expected_start = "stmts"
    elif compile_mode == "single":
        expected_start = "single_start"
    else:
        expected_start = None

    if expected_start:
        assert deparsed.ast == expected_start, (
            f"Should have parsed grammar start to '{expected_start}'; "
            f"got: {deparsed.ast.kind}"
        )
    # save memory
    del tokens

    deparsed.mod_globs, nonlocals = find_globals_and_nonlocals(
        deparsed.ast, set(), set(), co, version
    )

    deparsed.is_module = compile_mode not in (
        "dictcomp",
        "gencomp",
        "genexpr",
        "lambda",
        "listcomp",
        "setcomp",
    )

    if deparsed.is_module:
        assert not nonlocals

    deparsed.FUTURE_UNICODE_LITERALS = (
        COMPILER_FLAG_BIT["FUTURE_UNICODE_LITERALS"] & co.co_flags != 0
    )

    # What we've been waiting for: Generate source from Syntax Tree!
    deparsed.gen_source(
        deparsed.ast,
        name=co.co_name,
        customize=customize,
        is_lambda=is_lambda_mode(compile_mode),
        debug_opts=debug_opts,
    )

    for g in sorted(deparsed.mod_globs):
        deparsed.write("# global %s ## Warning: Unused global\n" % g)

    if deparsed.ast_errors:
        deparsed.write("# NOTE: have internal decompilation grammar errors.\n")
        deparsed.write("# Use -T option to show full context.")
        for err in deparsed.ast_errors:
            deparsed.write(err)
        raise SourceWalkerError("Deparsing hit an internal grammar-rule bug")

    if deparsed.ERROR:
        raise SourceWalkerError("Deparsing stopped due to parse error")
    return deparsed


def deparse_code2str(
    code,
    out=sys.stdout,
    version=None,
    debug_opts=DEFAULT_DEBUG_OPTS,
    code_objects={},
    compile_mode="exec",
    is_pypy=IS_PYPY,
    walker=SourceWalker,
    start_offset: int = 0,
    stop_offset: int = -1,
) -> str:
    """
    Return the deparsed text for a Python code object. `out` is where
    any intermediate output for assembly or tree output will be sent.
    """

    if out is None:
        out = sys.stdout

    tree = code_deparse(
        code,
        out,
        version,
        debug_opts,
        code_objects=code_objects,
        compile_mode=compile_mode,
        is_pypy=is_pypy,
        walker=walker,
        start_offset=start_offset,
        stop_offset=stop_offset,
    )

    return "# deparse failed" if tree is None else tree.text


if __name__ == "__main__":

    def deparse_test(co):
        """This is a docstring"""
        s = deparse_code2str(co)
        # s = deparse_code2str(co, debug_opts={"asm": "after", "tree": {'before': False, 'after': False}})
        print(s)
        return

    deparse_test(deparse_test.__code__)
