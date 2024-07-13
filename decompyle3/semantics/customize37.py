#  Copyright (c) 2019-2023 by Rocky Bernstein
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
"""Isolate Python 3.7 version-specific semantic actions here.
"""

import re

from spark_parser.ast import GenericASTTraversalPruningException
from xdis import co_flags_is_async, iscode

from decompyle3.parsers.treenode import SyntaxTree
from decompyle3.scanners.tok import Token
from decompyle3.semantics.consts import (
    INDENT_PER_LEVEL,
    PRECEDENCE,
    TABLE_DIRECT,
    TABLE_R,
)
from decompyle3.semantics.helper import escape_string, flatten_list, strip_quotes


def escape_format(s):
    return s.replace("\r", "\\r").replace("\n", "\\n").replace("'''", '"""')


EMPTY_DICT = SyntaxTree(
    "dict", [Token("BUILD_MAP_0", attr=0, pattr="", offset=0, has_arg=True)]
)

# FIXME: Get this from a newer xdis!
FSTRING_CONVERSION_MAP = {1: "!s", 2: "!r", 3: "!a", "X": ":X"}

#######################
def customize_for_version37(self, version):
    ########################
    # Python 3.7+ changes
    #######################

    # fmt: off
    PRECEDENCE["attribute37"]      =   2
    PRECEDENCE["call_ex"]          =   1
    PRECEDENCE["call_ex_kw"]       =   1
    PRECEDENCE["call_ex_kw2"]      =   1
    PRECEDENCE["call_ex_kw3"]      =   1
    PRECEDENCE["call_ex_kw4"]      =   1
    PRECEDENCE["call_kw"]          =   0
    PRECEDENCE["call_kw36"]        =   1
    # f"...". This has to be below "named_expr" to make f'{(x := 10)}'
    # preserve parenthesis
    PRECEDENCE["formatted_value1"] =  38
    PRECEDENCE["formatted_value2"] =  38  # See above
    PRECEDENCE["if_exp_37a"]       =  28
    PRECEDENCE["if_exp_37b"]       =  28
    PRECEDENCE["dict_unpack"]      =   0  # **{...}

    # fmt: on
    TABLE_DIRECT.update(
        {
            "and_parts": (
                "%P and %p",
                (0, -1, "and ", PRECEDENCE["and"]),
                (1, "expr_pjif", PRECEDENCE["and"]),
            ),
            "and_or_expr": (
                "%c and %c or %c",
                (0, "and_parts"),
                (1, "expr"),
                (2, "jitop_come_from_expr"),
            ),
            "or_and": (
                "%c or (%c and %c)",
                (0, "expr_jitop"),
                (1, "expr"),
                (4, "expr"),
            ),
            "or_and1": (
                "%p or %p",
                (0, "or_parts", PRECEDENCE["or"]),
                (1, "and_parts", PRECEDENCE["or"]),
            ),
            "and_or": (
                "%c and (%c or %c)",
                (0, "expr_jifop"),
                (1, "expr"),
                (4, "expr"),
            ),
            "and_not": ("%c and not %c", (0, "expr_pjif"), (1, "expr_pjit")),
            "and_cond": (
                "%c and %c",
                (0, ("and_parts", "testfalse")),
                (1, ("expr_pjif", "expr")),
            ),
            "ann_assign": (
                "%|%[2]{attr}: %c\n",
                0,
            ),
            "ann_assign_init": (
                "%|%[2]{attr}: %c = %c\n",
                0,
                1,
            ),
            "async_for_stmt": (
                "%|async for %c in %c:\n%+%c%-\n\n",
                (8, "store"),
                (1, "expr"),
                (-9, "for_block"),
            ),
            "async_for_stmt2": (
                "%|async for %c in %c:\n%+%c%-\n\n",
                (10, "store"),
                (1, "expr"),
                (-3, "for_block"),
            ),
            "async_for_stmt36": (
                "%|async for %c in %c:\n%+%c%-\n\n",
                (9, "store"),
                (1, "expr"),
                (18, "for_block"),
            ),
            "async_for_stmt37": (
                "%|async for %c in %c:\n%+%c%-\n\n",
                (8, "store"),
                (1, "expr"),
                (17, "for_block"),
            ),
            "async_with_stmt": ("%|async with %c:\n%+%c%-", (0, "expr"), 3),
            "async_with_as_stmt": (
                "%|async with %c as %p:\n%+%c%-",
                (0, "expr"),
                (2, "store", PRECEDENCE["unpack"] - 1),
                3,
            ),
            "async_forelse_stmt": (
                "%|async for %c in %c:\n%+%c%-%|else:\n%+%c%-\n\n",
                (8, "store"),
                (1, "expr"),
                (-10, "for_block"),
                (-2, "else_suite"),
            ),
            "attribute37": ("%c.%[1]{pattr}", (0, "expr")),
            "attributes37": (
                "%[0]{pattr} import %c",
                (0, "IMPORT_NAME_ATTR"),
                (1, "IMPORT_FROM"),
            ),
            # nested await expressions like:
            #   return await (await bar())
            # need parenthesis.
            # Note there are async dictionary expressions are like await expr's
            # the below is just the default fersion
            "await_expr": ("await %p", (0, PRECEDENCE["await_expr"] - 1)),
            "await_stmt": ("%|%c\n", 0),
            "c_async_with_stmt": ("%|async with %c:\n%+%c%-", (0, "expr"), 3),
            "call_ex": ("%c(%p)", (0, "expr"), (1, 100)),
            "compare_chained_middlea_37": (
                "%p %p",
                (0, PRECEDENCE["compare"] - 1),
                (1, PRECEDENCE["compare"] - 1),
            ),
            "c_compare_chained_middlea_37": (
                "%p %p",
                (0, PRECEDENCE["compare"] - 1),
                (1, PRECEDENCE["compare"] - 1),
            ),
            "compare_chained_middle_false_37": (
                "%p%p",
                (0, "chained_parts", PRECEDENCE["compare"] - 1),
                (1, PRECEDENCE["compare"] - 1),
            ),
            "compare_chained_right_false_37": (
                (0, "chained_part", PRECEDENCE["compare"] - 1),
                (1, PRECEDENCE["compare"] - 1),
            ),
            "compare_chained_middleb_false_37": (
                "%p %p",
                (0, PRECEDENCE["compare"] - 1),
                (1, PRECEDENCE["compare"] - 1),
            ),
            "chained_part": (
                ' %[3]{pattr.replace("-", " ")} %p',
                (0, "expr", PRECEDENCE["compare"] - 1),
            ),
            "compare_chained_and": (
                "%c%c and %c",
                (0, "expr"),
                (1, "chained_parts"),
                -2,  # Is often a transformed negated_testtrue
            ),
            "compare_chained_middlec_37": (
                "%p %p",
                (0, PRECEDENCE["compare"] - 1),
                (1, PRECEDENCE["compare"] - 1),
            ),
            "compare_chained_righta_37": (
                '%[1]{pattr.replace("-", " ")} %p',
                (0, PRECEDENCE["compare"] - 1),
            ),
            "c_compare_chained_righta_37": (
                '%[1]{pattr.replace("-", " ")} %p',
                (0, PRECEDENCE["compare"] - 1),
            ),
            "c_try_except36": ("%|try:\n%+%c%-%c\n\n", 1, 2),
            "compare_chained_rightb_false_37": (
                '%[1]{pattr.replace("-", " ")} %p',
                (0, PRECEDENCE["compare"] - 1),
            ),
            "c_compare_chained_rightb_false_37": (
                ' %[1]{pattr.replace("-", " ")} %p',
                (0, PRECEDENCE["compare"] - 1),
            ),
            "compare_chained_righta_false_37": (
                '%[1]{pattr.replace("-", " ")} %p',
                (0, PRECEDENCE["compare"] - 1),
            ),
            "c_compare_chained_righta_false_37": (
                ' %[1]{pattr.replace("-", " ")} %p',
                (0, PRECEDENCE["compare"] - 1),
            ),
            "compare_chained_rightc_37": (
                "%p %p",
                (0, PRECEDENCE["compare"] - 1),
                (1, PRECEDENCE["compare"] - 1),
            ),
            "c_try_except": ("%|try:\n%+%c%-%c\n\n", 1, (3, "c_except_handler")),
            "if_exp_compare": (
                "%p if %c else %c",
                (1, "expr", PRECEDENCE["if_exp"] - 1),
                (0, ("expr", "bool_op")),
                -2,  # Must be from end since beginnings might not match
            ),
            "dict_unpack": ("{**%C}", (0, -1, ", **")),
            "except_return": ("%|except:\n%+%c%-", 3),
            "if_exp_37a": (
                "%p if %p else %p",
                (1, "expr", PRECEDENCE["if_exp"] - 1),
                (0, PRECEDENCE["if_exp"] - 1),
                (4, "expr", PRECEDENCE["if_exp"] - 1),
            ),
            "if_exp_37b": (
                "%p if %p else %p",
                (1, "expr_pjif", PRECEDENCE["if_exp"] - 1),
                (0, "expr_pjif", PRECEDENCE["if_exp"] - 1),
                (3, "expr", PRECEDENCE["if_exp"] - 1),
            ),
            "if_not_stmtc": (
                "%|if not %c:\n%+%c%-",
                (0, "testexprc"),
                (1, "ifstmts_jumpc"),
            ),
            "ifstmt_bool": (
                "%|if %c:\n%+%c%-",
                (0, ("or_and_not", "or_and1")),
                (1, "stmts"),
            ),
            "ifstmtc": (
                "%|if %c:\n%+%c%-",
                (0, ("testexpr", "testexprc")),
                (1, "ifstmts_jumpc"),
            ),
            "if_and_elsestmtc": (
                "%|if %c and %c:\n%+%c%-%|else:\n%+%c%-",
                (0, "expr_pjif"),
                (1, "expr_pjif"),
                (2, "c_stmts"),
                (-2, "else_suitec"),
            ),
            "if_and_stmt": (
                "%|if %c and %c:\n%+%c%-",
                (0, "expr_pjif"),
                (1, "expr"),
                (3, "stmts"),
            ),
            "if_or_stmt": (
                "%|if %c or %c:\n%+%c%-",
                (0, "expr"),
                (2, "expr"),
                (5, "stmts"),
            ),
            "if_or_elsestmt": (
                "%|if %c or %c:\n%+%c%-%|else:\n%+%c%-",
                (0, "expr"),
                (3, "expr"),
                (6, "stmts"),
                (-2, "else_suite"),
            ),
            "if_or_not_elsestmt": (
                "%|if %c or not %c:\n%+%c%-%|else:\n%+%c%-",
                (0, "expr"),
                (3, "expr"),
                (6, "stmts"),
                (-2, "else_suite"),
            ),
            "import_from37": ("%|from %[2]{pattr} import %c\n", (3, "importlist37")),
            "import_from_as37": (
                "%|from %c as %c\n",
                (2, "import_from_attr37"),
                (3, "store"),
            ),
            "import_one": (
                "%c",
                (0, "importlists"),
            ),
            "importattr37": ("%c", (0, "IMPORT_NAME_ATTR")),
            "import_from_attr37": (
                "%c import %c",
                (0, "IMPORT_NAME_ATTR"),
                (1, "IMPORT_FROM"),
            ),
            "list_afor": (
                " async for %[1]{%c} in %c%[1]{%c}",
                (1, "store"),
                (0, "get_aiter"),
                (3, "list_iter"),
            ),
            "list_if37": (" if %p%c", (0, 27), 1),
            "list_if37_not": (" if not %p%c", (0, 27), 1),
            # This is eliminated in the transform phase, but
            # we have it here to be logically complete and more robust
            # if something goes wrong.
            "negated_testtrue": (
                "not %c",
                (0, "testtrue"),
            ),
            "not_and_not": (
                "%c and not %c",
                (0, "not"),
                (1, "expr_pjif"),
            ),
            "nor_cond": (
                "%c or %c",
                (0, ("or_parts", "and")),
                (1, "expr_pjif"),
            ),
            "or_and_not": (
                "%c or %c",
                (0, "expr_pjit"),
                (1, "and_not"),
            ),
            "or_cond": (
                "%c or %c",
                (0, ("or_parts", "and", "not_and_not")),
                (1, "expr_pjif"),
            ),
            "or_cond1": (
                "%c or %c",
                (0, ("or_parts", "and")),
                (-2, "expr_pjif"),
            ),
            "and_or_cond": (
                "%c and %c or %c",
                (0, ("and_parts", "or_parts")),
                (1, "expr"),
                (4, "expr_pjif"),
            ),
            "not": (
                "not %p",
                (0, "expr_pjit", PRECEDENCE["not"]),
            ),
            "not_or": (
                "not %p or %c",
                (0, "and_parts", PRECEDENCE["and"] - 1),
                (1, "expr_pjif"),
            ),
            "nand": (
                "not (%c and %c)",
                (0, "and_parts"),
                (1, ("expr", "expr_pjit")),
            ),
            "c_nand": (
                "not (%c and %c)",
                (0, "and_parts"),
                (1, "expr_pjitt"),
            ),
            "or_parts": (
                "%P or %p",
                (0, -1, " or ", PRECEDENCE["or"]),
                (1, ("expr_pjif", "expr_pjit"), PRECEDENCE["or"]),
            ),
            "store_async_iter_end": ("%c", (0, "store")),
            "testfalsec": (
                "not %c",
                (
                    0,
                    (
                        "expr",
                        "c_compare_chained37_false",
                        "c_compare_chained_middleb_false_37",
                        "c_nand",
                    ),
                ),
            ),
            "try_except36": ("%|try:\n%+%c%-%c\n\n", 1, -2),
            "tryfinally36": ("%|try:\n%+%c%-%|finally:\n%+%c%-\n\n", (1, "returns"), 3),
            "tryfinally_return_stmt1": (
                "%|try:\n%+%c%-%|finally:\n%+%c%-\n\n",
                (1, "suite_stmts_opt"),
                (-1, "returns"),
            ),
            "tryfinally_return_stmt2": (
                "%|try:\n%+%c%-%|finally:\n%+%|return %c%-\n\n",
                (1, "suite_stmts_opt"),
                3,
            ),
            "unpack_list": ("*%c", (0, "list")),
            "yield_from": ("yield from %c", (0, "expr")),
        }
    )

    TABLE_R.update(
        {
            "CALL_FUNCTION_EX": ("%c(*%P)", 0, (1, 2, ", ", 100)),
            # Not quite right
            "CALL_FUNCTION_EX_KW": ("%c(**%C)", 0, (2, 3, ",")),
        }
    )

    def call36_tuple(node):
        """
        A tuple used in a call, these are like normal tuples but they
        don't have the enclosing parenthesis.
        """
        assert node == "tuple"
        # Note: don't iterate over last element which is a
        # BUILD_TUPLE...
        flat_elems = flatten_list(node[:-1])

        self.indent_more(INDENT_PER_LEVEL)
        sep = ""

        for elem in flat_elems:
            if elem in ("ROT_THREE", "EXTENDED_ARG"):
                continue
            assert elem == "expr"
            line_number = self.line_number
            value = self.traverse(elem)
            if line_number != self.line_number:
                sep += "\n" + self.indent + INDENT_PER_LEVEL[:-1]
            self.write(sep, value)
            sep = ", "

        self.indent_less(INDENT_PER_LEVEL)
        return len(flat_elems)

    self.call36_tuple = call36_tuple

    def call36_dict(node):
        """
        A dict used in a call_ex_kw2, which are a dictionary items expressed
        in a call. This should format to:
             a=1, b=2
        In other words, no braces, no quotes around keys and ":" becomes
        "=".

        We will source-code use line breaks to guide us when to break.
        """
        p = self.prec
        self.prec = 100

        self.indent_more(INDENT_PER_LEVEL)
        sep = INDENT_PER_LEVEL[:-1]
        line_number = self.line_number

        if node[0].kind.startswith("kvlist"):
            # Python 3.5+ style key/value list in dict
            kv_node = node[0]
            ll = list(kv_node)
            i = 0

            length = len(ll)
            # FIXME: Parser-speed improved grammars will have BUILD_MAP
            # at the end. So in the future when everything is
            # complete, we can do an "assert" instead of "if".
            if kv_node[-1].kind.startswith("BUILD_MAP"):
                length -= 1

            # Respect line breaks from source
            while i < length:
                self.write(sep)
                name = self.traverse(ll[i], indent="")
                # Strip off beginning and trailing quotes in name
                name = name[1:-1]
                if i > 0:
                    line_number = self.indent_if_source_nl(
                        line_number, self.indent + INDENT_PER_LEVEL[:-1]
                    )
                line_number = self.line_number
                self.write(name, "=")
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
        elif node[-1].kind.startswith("BUILD_CONST_KEY_MAP"):
            keys_node = node[-2]
            keys = keys_node.attr
            # from trepan.api import debug; debug()
            assert keys_node == "LOAD_CONST" and isinstance(keys, tuple)
            for i in range(node[-1].attr):
                self.write(sep)
                self.write(keys[i], "=")
                value = self.traverse(node[i], indent="")
                self.write(value)
                sep = ", "
                if line_number != self.line_number:
                    sep += "\n" + self.indent + INDENT_PER_LEVEL[:-1]
                    line_number = self.line_number
                    pass
                pass
        else:
            self.write("**")
            try:
                if node == EMPTY_DICT:
                    self.write("{}")
                else:
                    self.default(node)
            except GenericASTTraversalPruningException:
                pass

        self.prec = p
        self.indent_less(INDENT_PER_LEVEL)
        return

    self.call36_dict = call36_dict

    def gen_function_parens_adjust(mapping_key, node):
        """If we can avoid the outer parenthesis
        of a generator function, set the node key to
        'call_generator' and the caller will do the default
        action on that. Otherwise we do nothing.
        """
        if mapping_key.kind != "CALL_FUNCTION_1":
            return

        args_node = node[-2]
        if args_node == "pos_arg":
            assert args_node[0] == "expr"
            n = args_node[0][0]
            if n == "generator_exp":
                node.kind = "call_generator"
            pass
        return

    # FIXME: Can we to compress this into a single template?
    def n_and_parts(node):
        if len(node) == 1:
            self.template_engine(("%c", (0, "expr_pjif")), node)
            self.prune()
        else:
            self.default(node)
            pass
        return

    self.n_and_parts = n_and_parts

    def n_await_expr(node):
        dict_comp_async = node[0][0]
        if dict_comp_async == "dict_comp_async":
            compile_mode = self.compile_mode
            self.compile_mode = "dictcomp"
            try:
                self.n_set_comp(dict_comp_async)
            except GenericASTTraversalPruningException:
                pass
            self.compile_mode = compile_mode
        else:
            self.default(node)
        self.prune()
        return

    self.n_await_expr = n_await_expr

    # FIXME: we should be able to compress this into a single template
    def n_or_parts(node):
        if len(node) == 1:
            self.template_engine(("%c", (0, "expr_pjit", "expr_pjif")), node)
            self.prune()
        else:
            self.default(node)
            pass
        return

    self.n_or_parts = n_or_parts

    self.n_and_parts = n_and_parts

    def n_assert_invert(node):
        testtrue = node[0]
        assert testtrue == "testtrue"
        testtrue.kind = "assert"
        self.default(testtrue)

    self.n_assert_invert = n_assert_invert

    def n_async_call(node):
        self.f.write("async ")
        node.kind = "call"
        p = self.prec
        self.prec = 80
        self.template_engine(("%c(%P)", 0, (1, -4, ", ", 100)), node)
        self.prec = p
        node.kind = "async_call"
        self.prune()

    self.n_async_call = n_async_call

    def n_attribute37(node):
        expr = node[0]
        assert expr == "expr"
        if expr[0] == "LOAD_CONST":
            # FIXME: I didn't record which constants parenthesis is
            # necessary. However, I suspect that we could further
            # refine this by looking at operator precedence and
            # eval'ing the constant value (pattr) and comparing with
            # the type of the constant.
            node.kind = "attribute_w_parens"
        self.default(node)

    self.n_attribute37 = n_attribute37

    def n_build_list_unpack(node):
        """
        prettyprint a list or tuple
        """
        p = self.prec
        self.prec = 100
        lastnode = node.pop()
        lastnodetype = lastnode.kind

        # If this build list is inside a CALL_FUNCTION_VAR,
        # then the first * has already been printed.
        # Until I have a better way to check for CALL_FUNCTION_VAR,
        # will assume that if the text ends in *.
        last_was_star = self.f.getvalue().endswith("*")

        if lastnodetype.startswith("BUILD_LIST"):
            self.write("[")
            endchar = "]"
        else:
            endchar = ""

        flat_elems = flatten_list(node)

        self.indent_more(INDENT_PER_LEVEL)
        sep = ""
        for elem in flat_elems:
            if elem in ("ROT_THREE", "EXTENDED_ARG"):
                continue
            assert elem == "expr"
            line_number = self.line_number
            use_star = True
            value = self.traverse(elem)
            if value.startswith("("):
                assert value.endswith(")")
                use_star = False
                value = value[1:-1].rstrip(
                    " "
                )  # Remove starting '(' and trailing ')' and additional spaces
                if value == "":
                    pass
                else:
                    if value.endswith(","):  # if args has only one item
                        value = value[:-1]
            if line_number != self.line_number:
                sep += "\n" + self.indent + INDENT_PER_LEVEL[:-1]
            else:
                if sep != "":
                    sep += " "
            if not last_was_star and use_star:
                sep += "*"
                pass
            else:
                last_was_star = False
            self.write(sep, value)
            sep = ","
        self.write(endchar)
        self.indent_less(INDENT_PER_LEVEL)

        self.prec = p
        self.prune()
        return

    self.n_build_list_unpack = n_build_list_unpack

    def n_c_with(node):
        if len(node) == 1 and node[0] == "with":
            node = node[0]
        else:
            node.kind = "with"
        self.default(node)

    self.n_c_with = n_c_with

    def n_c_except_suite(node):
        node_len = len(node)
        if node_len == 1 and node[0] in ("except_suite", "c_returns"):
            node = node[0]
            self.default(node)
        elif node[1] in ("c_suite_stmts", "c_except_suite"):
            node = node[1][0]
            template = ("%+%c%-", 0)
            self.template_engine(template, node)
            self.prune()

    self.n_c_except_suite = n_c_except_suite

    self.n_c_with = n_c_with

    def n_call(node):
        p = self.prec
        self.prec = 100
        mapping = self._get_mapping(node)
        table = mapping[0]
        key = node
        for i in mapping[1:]:
            key = key[i]
            pass
        opname = key.kind
        if opname.startswith("CALL_FUNCTION_VAR_KW"):
            # Python 3.5 changes the stack position of
            # *args: kwargs come after *args whereas
            # in earlier Pythons, *args is at the end
            # which simplifies things from our
            # perspective.  Python 3.6+ replaces
            # CALL_FUNCTION_VAR_KW with
            # CALL_FUNCTION_EX We will just swap the
            # order to make it look like earlier
            # Python 3.
            entry = table[key.kind]
            kwarg_pos = entry[2][1]
            args_pos = kwarg_pos - 1
            # Put last node[args_pos] after subsequent kwargs
            while node[kwarg_pos] == "kwarg" and kwarg_pos < len(node):
                # swap node[args_pos] with node[kwargs_pos]
                node[kwarg_pos], node[args_pos] = node[args_pos], node[kwarg_pos]
                args_pos = kwarg_pos
                kwarg_pos += 1
        elif opname.startswith("CALL_FUNCTION_VAR"):
            # CALL_FUNCTION_VAR's top element of the stack contains
            # the variable argument list, then comes
            # annotation args, then keyword args.
            # In the most least-top-most stack entry, but position 1
            # in node order, the positional args.
            argc = node[-1].attr
            nargs = argc & 0xFF
            kwargs = (argc >> 8) & 0xFF
            # FIXME: handle annotation args
            if nargs > 0:
                template = ("%c(%P, ", 0, (1, nargs + 1, ", ", 100))
            else:
                template = ("%c(", 0)
            self.template_engine(template, node)

            args_node = node[-2]
            if args_node in ("pos_arg", "expr"):
                args_node = args_node[0]
            if args_node == "build_list_unpack":
                template = ("*%P)", (0, len(args_node) - 1, ", *", 100))
                self.template_engine(template, args_node)
            else:
                if len(node) - nargs > 3:
                    template = (
                        "*%c, %P)",
                        nargs + 1,
                        (nargs + kwargs + 1, -1, ", ", 100),
                    )
                else:
                    template = ("*%c)", nargs + 1)
                self.template_engine(template, node)
            self.prec = p
            self.prune()
        elif (
            opname.startswith("CALL_FUNCTION_1")
            and opname == "CALL_FUNCTION_1"
            or not re.match(r"\d", opname[-1])
        ):
            template = "(%c)(%p)" if node[0][0] == "lambda_body" else "%c(%p)"
            self.template_engine(
                (template, (0, "expr"), (1, PRECEDENCE["yield"] - 1)), node
            )
            self.prec = p
            self.prune()
        else:
            gen_function_parens_adjust(key, node)

        self.prec = p
        self.default(node)

    self.n_call = n_call

    def n_classdef36(node):
        # class definition ('class X(A,B,C):')
        cclass = self.currentclass

        # Pick out various needed bits of information
        # * class_name - the name of the class
        # * subclass_info - the parameters to the class  e.g.
        #      class Foo(bar, baz)
        #               ----------
        # * subclass_code - the code for the subclass body
        subclass_info = None
        if node == "classdefdeco2":
            if isinstance(node[1][1].attr, str):
                class_name = node[1][1].attr
                if self.is_pypy and class_name.find("<locals>") > 0:
                    class_name = class_name.split(".")[-1]

            else:
                class_name = node[1][2].attr
            build_class = node
        else:
            build_class = node[0]
            if build_class == "build_class_kw":
                mkfunc = build_class[1]
                assert mkfunc == "mkfunc"
                subclass_info = build_class
                if hasattr(mkfunc[0], "attr") and iscode(mkfunc[0].attr):
                    subclass_code = mkfunc[0].attr
                else:
                    assert mkfunc[0] == "load_closure"
                    subclass_code = mkfunc[1].attr
                    assert iscode(subclass_code)
            if build_class[1][0] == "load_closure":
                code_node = build_class[1][1]
            else:
                code_node = build_class[1][0]
            class_name = code_node.attr.co_name

        assert "mkfunc" == build_class[1]
        mkfunc = build_class[1]
        if mkfunc[0] in ("kwargs", "no_kwargs"):
            for n in mkfunc:
                if hasattr(n, "attr") and iscode(n.attr):
                    subclass_code = n.attr
                    break
                pass
            if node == "classdefdeco2":
                subclass_info = node
            else:
                subclass_info = node[0]
        elif build_class[1][0] == "load_closure":
            # Python 3 with closures not functions
            load_closure = build_class[1]
            subclass_code = None
            for i in range(-4, -1):
                if load_closure[i] == "LOAD_CODE":
                    subclass_code = load_closure[i].attr
                    break
            if subclass_code is None:
                raise RuntimeError(
                    "Internal Error n_classdef: cannot find " "class body"
                )
            if hasattr(build_class[3], "__len__"):
                if not subclass_info:
                    subclass_info = build_class[3]
            elif hasattr(build_class[2], "__len__"):
                subclass_info = build_class[2]
            else:
                raise RuntimeError(
                    "Internal Error n_classdef: cannot " "superclass name"
                )
        elif node == "classdefdeco2":
            subclass_info = node
            subclass_code = build_class[1][0].attr
        elif not subclass_info:
            if mkfunc[0] in ("no_kwargs", "kwargs"):
                subclass_code = mkfunc[1].attr
            else:
                subclass_code = mkfunc[0].attr
            if node == "classdefdeco2":
                subclass_info = node
            else:
                subclass_info = node[0]

        if node == "classdefdeco2":
            self.write("\n")
        else:
            self.write("\n\n")

        self.currentclass = str(class_name)
        self.write(self.indent, "class ", self.currentclass)

        self.print_super_classes3(subclass_info)
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

    self.n_classdef36 = n_classdef36

    def n_compare_chained(node):
        if node[0] in (
            "c_compare_chained37",
            "c_compare_chained37_false",
            "compare_chained37",
            "compare_chained37_false",
        ):
            self.default(node[0])
        else:
            self.default(node)

    self.n_compare_chained = self.n_c_compare_chained = n_compare_chained

    def n_importlist37(node):
        if len(node) == 1:
            self.default(node)
            return
        n = len(node) - 1
        i = -1
        for i in range(n, -1, -1):
            if node[i] != "ROT_TWO":
                break
        self.template_engine(("%C", (0, i + 1, ", ")), node)
        self.prune()
        return

    self.n_importlist37 = n_importlist37

    def n_call_kw36(node):
        self.template_engine(("%p(", (0, 100)), node)
        keys = node[-2].attr
        num_kwargs = len(keys)
        num_posargs = len(node) - (num_kwargs + 2)
        n = len(node)
        assert n >= len(keys) + 1, "not enough parameters keyword-tuple values"
        sep = ""

        line_number = self.line_number
        for i in range(1, num_posargs):
            self.write(sep)
            self.preorder(node[i])
            if line_number != self.line_number:
                sep = ",\n" + self.indent + "  "
            else:
                sep = ", "
            line_number = self.line_number

        i = num_posargs
        j = 0
        # FIXME: adjust output for line breaks?
        while i < n - 2:
            self.write(sep)
            self.write(keys[j] + "=")
            self.preorder(node[i])
            if line_number != self.line_number:
                sep = ",\n" + self.indent + "  "
            else:
                sep = ", "
            i += 1
            j += 1
        self.write(")")
        self.prune()
        return

    self.n_call_kw36 = n_call_kw36

    def is_async_fn(node):
        code_node = node[0][0]
        for n in node[0]:
            if hasattr(n, "attr") and iscode(n.attr):
                code_node = n
                break
            pass
        pass

        is_code = hasattr(code_node, "attr") and iscode(code_node.attr)
        return is_code and co_flags_is_async(code_node.attr.co_flags)

    def n_function_def(node):
        if is_async_fn(node):
            self.template_engine(("\n\n%|async def %c\n", -2), node)
        else:
            self.default(node)
        self.prune()

    self.n_function_def = n_function_def

    def n_import_from(node):
        relative_path_index = 0
        if node[relative_path_index].attr > 0:
            node[2].pattr = ("." * node[relative_path_index].attr) + node[2].pattr
        if isinstance(node[1].attr, tuple):
            imports = node[1].attr
            for pattr in imports:
                node[1].pattr = pattr
                self.default(node)
            return
        self.default(node)

    self.n_import_from = n_import_from
    self.n_import_from_star = n_import_from

    def n_mkfuncdeco0(node):
        if is_async_fn(node):
            self.template_engine(("%|async def %c\n", 0), node)
        else:
            self.default(node)
        self.prune()

    self.n_mkfuncdeco0 = n_mkfuncdeco0

    def n_unmapexpr(node):
        last_n = node[0][-1]
        for n in node[0]:
            self.preorder(n)
            if n != last_n:
                self.f.write(", **")
                pass
            pass
        self.prune()
        pass

    self.n_unmapexpr = n_unmapexpr

    # FIXME: start here
    def n_list_unpack(node):
        """
        prettyprint an unpacked list or tuple
        """
        p = self.prec
        self.prec = 100
        lastnode = node.pop()
        lastnodetype = lastnode.kind

        # If this build list is inside a CALL_FUNCTION_VAR,
        # then the first * has already been printed.
        # Until I have a better way to check for CALL_FUNCTION_VAR,
        # will assume that if the text ends in *.
        last_was_star = self.f.getvalue().endswith("*")

        if lastnodetype.startswith("BUILD_LIST"):
            self.write("[")
            endchar = "]"
        elif lastnodetype.startswith("BUILD_TUPLE"):
            # Tuples can appear places that can NOT
            # have parenthesis around them, like array
            # subscripts. We check for that by seeing
            # if a tuple item is some sort of slice.
            no_parens = False
            for n in node:
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

        elif lastnodetype.startswith("BUILD_SET"):
            self.write("{")
            endchar = "}"
        elif lastnodetype.startswith("BUILD_MAP_UNPACK"):
            self.write("{*")
            endchar = "}"
        elif lastnodetype.startswith("ROT_TWO"):
            self.write("(")
            endchar = ")"
        else:
            raise TypeError(
                "Internal Error: n_build_list expects list, tuple, set, or unpack"
            )

        flat_elems = flatten_list(node)

        self.indent_more(INDENT_PER_LEVEL)
        sep = ""
        for elem in flat_elems:
            if elem in ("ROT_THREE", "EXTENDED_ARG"):
                continue
            assert elem == "expr"
            line_number = self.line_number
            value = self.traverse(elem)
            if elem[0] == "tuple":
                assert value[0] == "("
                assert value[-1] == ")"
                value = value[1:-1]
                if value[-1] == ",":
                    # singleton tuple
                    value = value[:-1]
            else:
                value = "*" + value
            if line_number != self.line_number:
                sep += "\n" + self.indent + INDENT_PER_LEVEL[:-1]
            else:
                if sep != "":
                    sep += " "
            if not last_was_star:
                pass
            else:
                last_was_star = False
            self.write(sep, value)
            sep = ","
        if lastnode.attr == 1 and lastnodetype.startswith("BUILD_TUPLE"):
            self.write(",")
        self.write(endchar)
        self.indent_less(INDENT_PER_LEVEL)

        self.prec = p
        self.prune()
        return

    self.n_tuple_unpack = n_list_unpack

    def n_build_unpack_tuple_with_call(node):
        n = node[0]
        if n == "expr":
            n = n[0]
        if n == "tuple":
            self.call36_tuple(n)
            first = 1
            sep = ", *"
        elif n in ("LOAD_CONST", "LOAD_STR"):
            value = self.format_pos_args(n)
            self.f.write(value)
            first = 1
            sep = ", *"
        else:
            first = 0
            sep = "*"

        buwc = node[-1]
        assert buwc.kind.startswith("BUILD_TUPLE_UNPACK_WITH_CALL")
        for n in node[first:-1]:
            self.f.write(sep)
            self.preorder(n)
            sep = ", *"
            pass
        self.prune()
        return

    self.n_build_tuple_unpack_with_call = n_build_unpack_tuple_with_call

    def n_build_unpack_map_with_call(node):
        n = node[0]
        if n == "expr":
            n = n[0]
        if n == "dict":
            self.call36_dict(n)
            first = 1
            sep = ", **"
        else:
            first = 0
            sep = "**"
        for n in node[first:-1]:
            self.f.write(sep)
            self.preorder(n)
            sep = ", **"
            pass
        self.prune()
        return

    self.n_build_map_unpack_with_call = n_build_unpack_map_with_call

    def n_call_ex_kw(node):
        """Handle CALL_FUNCTION_EX 1 (have KW) but with
        BUILD_MAP_UNPACK_WITH_CALL"""

        expr = node[1]
        assert expr == "expr"

        value = self.format_pos_args(expr)
        if value == "":
            fmt = "%c(%p)"
        else:
            fmt = "%c" + ("(%s, " % value).replace("%", "%%") + "%p)"

        self.template_engine(
            (fmt, (0, "expr"), (2, "build_map_unpack_with_call", 100)), node
        )

        self.prune()

    self.n_call_ex_kw = n_call_ex_kw

    def n_call_ex_kw2(node):
        """Handle CALL_FUNCTION_EX 2  (have KW) but with
        BUILD_{MAP,TUPLE}_UNPACK_WITH_CALL"""

        assert node[1] == "build_tuple_unpack_with_call"
        value = self.format_pos_args(node[1])
        if value == "":
            fmt = "%c(%p)"
        else:
            fmt = "%c" + ("(%s, " % value).replace("%", "%%") + "%p)"

        self.template_engine(
            (fmt, (0, "expr"), (2, "build_map_unpack_with_call", 100)), node
        )

        self.prune()

    self.n_call_ex_kw2 = n_call_ex_kw2

    def call_ex_kw3(node):
        """Handle CALL_FUNCTION_EX 1 (have KW) but without
        BUILD_MAP_UNPACK_WITH_CALL"""
        self.preorder(node[0])
        self.write("(")

        value = self.format_pos_args(node[1][0])
        if value == "":
            pass
        else:
            self.write(value)
            self.write(", ")

        self.write("*")
        self.preorder(node[1][1])
        self.write(", ")

        kwargs = node[2]
        if kwargs == "expr":
            kwargs = kwargs[0]
        if kwargs == "expr" and kwargs[0] != "dict":
            self.call36_dict(kwargs)
        else:
            self.write("**")
            self.preorder(kwargs)
        self.write(")")
        self.prune()

    self.n_call_ex_kw3 = call_ex_kw3

    def call_ex_kw4(node):
        """Handle CALL_FUNCTION_EX {1 or 2} but without
        BUILD_{MAP,TUPLE}_UNPACK_WITH_CALL"""
        self.preorder(node[0])
        self.write("(")
        args = node[1][0]
        if args == "tuple":
            if self.call36_tuple(args) > 0:
                self.write(", ")
                pass
            pass
        else:
            self.write("*")
            self.preorder(args)
            self.write(", ")
            pass

        kwargs = node[2]
        if kwargs == "expr":
            kwargs = kwargs[0]
        call_function_ex = node[-1]
        assert call_function_ex == "CALL_FUNCTION_EX_KW" or (
            self.version >= 3.6 and call_function_ex == "CALL_FUNCTION_EX"
        )
        # FIXME: decide if the below test be on kwargs == 'dict'
        if (
            call_function_ex.attr & 1
            and (not isinstance(kwargs, Token) and kwargs != "attribute")
            and kwargs != "call_kw36"
            and not kwargs[0].kind.startswith("kvlist")
        ):
            self.call36_dict(kwargs)
        else:
            self.write("**")
            self.preorder(kwargs)
        self.write(")")
        self.prune()

    self.n_call_ex_kw4 = call_ex_kw4

    # NOTE! This is different from decompyle3's version
    # Reconcile?
    def format_pos_args(node):
        """
        Positional args should format to:
        (*(2, ), ...) -> (2, ...)
        We remove starting and trailing parenthesis and ', ' if
        tuple has only one element.
        """
        value = self.traverse(node, indent="")
        if value.startswith("("):
            assert value.endswith(")")
            value = value[1:-1].rstrip(
                " "
            )  # Remove starting '(' and trailing ')' and additional spaces
            if value == "":
                pass  # args is empty
            else:
                if value.endswith(","):  # if args has only one item
                    value = value[:-1]
        return value

    self.format_pos_args = format_pos_args

    def n_except_suite_finalize(node):
        if node[1] == "returns" and self.hide_internal:
            # Process node[1] only.
            # The code after "returns", e.g. node[3], is dead code.
            # Adding it is wrong as it dedents and another
            # exception handler "except_stmt" afterwards.
            # Note it is also possible that the grammar is wrong here.
            # and this should not be "except_stmt".
            self.indent_more()
            self.preorder(node[1])
            self.indent_less()
        else:
            self.default(node)
        self.prune()

    self.n_except_suite_finalize = n_except_suite_finalize

    def n_formatted_value(node):
        if node[0] in ("LOAD_STR", "LOAD_CONST"):
            value = node[0].attr
            if isinstance(value, tuple):
                self.write(node[0].attr)
            else:
                self.write(escape_string(node[0].attr))
            self.prune()
        else:
            self.default(node)

    self.n_formatted_value = n_formatted_value

    def n_formatted_value_attr(node):
        f_conversion(node)
        fmt_node = node.data[3]
        if fmt_node == "expr" and fmt_node[0] == "LOAD_STR":
            node.string = escape_format(fmt_node[0].attr)
        else:
            node.string = fmt_node
        self.default(node)

    self.n_formatted_value_attr = n_formatted_value_attr

    def f_conversion(node):
        fmt_node = node.data[1]
        if fmt_node == "expr" and fmt_node[0] == "LOAD_STR":
            data = fmt_node[0].attr
        else:
            data = fmt_node.attr
        node.conversion = FSTRING_CONVERSION_MAP.get(data, "")
        return node.conversion

    def n_formatted_value1(node):
        expr = node[0]
        assert expr == "expr"
        conversion = f_conversion(node)
        if self.in_format_string and self.in_format_string != "formatted_value1":
            value = self.traverse(expr, indent="")
            if value[0] == "{":
                # If we have a set or dictionary comprehension, then we need to add a space
                # so as not to confuse the format string with {{.
                fmt = "{ %s%s }"
            else:
                fmt = "{%s%s}"
            es = escape_string(fmt % (value, conversion))
            f_str = "%s" % es
        else:
            old_in_format_string = self.in_format_string
            self.in_format_string = "formatted_value1"
            value = self.traverse(expr, indent="")
            self.in_format_string = old_in_format_string
            es = escape_string("{%s%s}" % (value, conversion))
            f_str = "f%s" % es

        self.write(f_str)
        self.prune()

    self.n_formatted_value1 = n_formatted_value1

    def n_formatted_value2(node):
        p = self.prec
        self.prec = 100

        expr = node[0]
        assert expr == "expr"
        old_in_format_string = self.in_format_string
        self.in_format_string = "formatted_value2"
        value = self.traverse(expr, indent="")
        format_value_attr = node[-1]
        assert format_value_attr == "FORMAT_VALUE_ATTR"
        attr = format_value_attr.attr
        if attr & 4:
            assert node[1] == "expr"
            fmt = strip_quotes(self.traverse(node[1], indent=""))
            attr_flags = attr & 3
            if attr_flags:
                conversion = "%s:%s" % (FSTRING_CONVERSION_MAP.get(attr_flags, ""), fmt)
            else:
                conversion = ":%s" % fmt
        else:
            conversion = FSTRING_CONVERSION_MAP.get(attr, "")

        self.in_format_string = old_in_format_string
        f_str = "f%s" % escape_string("{%s%s}" % (value, conversion))
        self.write(f_str)

        self.prec = p
        self.prune()

    self.n_formatted_value2 = n_formatted_value2

    def n_joined_str(node):
        p = self.prec
        self.prec = 100

        old_in_format_string = self.in_format_string
        self.in_format_string = "joined_str"
        result = ""
        for expr in node[:-1]:
            assert expr == "expr"
            value = self.traverse(expr, indent="")
            if expr[0].kind.startswith("formatted_value"):
                # remove leading 'f'
                if value.startswith("f"):
                    value = value[1:]
                pass
            else:
                # {{ and }} in Python source-code format strings mean
                # { and } respectively. But only when *not* part of a
                # formatted value. However, in the LOAD_STR
                # bytecode, the escaping of the braces has been
                # removed. So we need to put back the braces escaping in
                # reconstructing the source.
                assert expr[0] == "LOAD_STR"
                value = value.replace("{", "{{").replace("}", "}}")

            # Remove leading quotes
            result += strip_quotes(value)
            pass
        self.in_format_string = old_in_format_string
        if self.in_format_string:
            self.write(result)
        else:
            self.write("f%s" % escape_string(result))

        self.prec = p
        self.prune()

    self.n_joined_str = n_joined_str

    def return_closure(node):
        # Nothing should be output here
        self.prune()
        return

    self.n_return_closure = return_closure
    # def kwargs_only_36(node):
    #     keys = node[-1].attr
    #     num_kwargs = len(keys)
    #     values = node[:num_kwargs]
    #     for i, (key, value) in enumerate(zip(keys, values)):
    #         self.write(key + '=')
    #         self.preorder(value)
    #         if i < num_kwargs:
    #             self.write(',')
    #     self.prune()
    #     return
    # self.n_kwargs_only_36 = kwargs_only_36

    def n_starred(node):
        node_len = len(node)
        assert node_len > 0
        pos_args = node[0]
        if pos_args == "expr":
            pos_args = pos_args[0]
        if pos_args == "tuple":
            build_tuple = pos_args[0]
            if build_tuple.kind.startswith("BUILD_TUPLE"):
                tuple_len = 0
            else:
                tuple_len = len(node) - 1
            star_start = 1
            template = "%C", (0, -1, ", ")
            self.template_engine(template, pos_args)
            if tuple_len == 0:
                self.write("*()")
                # That's it
                self.prune()
            self.write(", ")
        else:
            star_start = 0
        if node_len > 1:
            template = ("*%C", (star_start, -1, ", *"))
        else:
            template = ("*%c", (star_start, "expr"))

        self.template_engine(template, node)
        self.prune()

    self.n_starred = n_starred

    def n_set_afor(node):
        if len(node) == 2:
            self.template_engine(
                (" async for %[1]{%c} in %c", (1, "store"), (0, "get_aiter")), node
            )
        else:
            self.template_engine(
                " async for %[1]{%c} in %c%c",
                (1, "store"),
                (0, "get_aiter"),
                (2, "set_iter"),
            )
        self.prune()

    self.n_set_afor = n_set_afor

    # FIXME: The following adjusts I guess a bug in the parser.
    # It might be as simple as renaming grammar symbol "testtrue" to "testtrue_or_false"
    # and then keeping this as is with the name change.
    # Fixing in the parsing by inspection is harder than doing it here.
    def n_testtrue(node):
        compare_chained37 = node[0]
        if (
            compare_chained37 == "compare_chained37"
            and compare_chained37[1] == "compare_chained_middleb_37"
        ):
            compare_chained_middleb_37 = compare_chained37[1]
            if (
                len(compare_chained_middleb_37) > 2
                and compare_chained_middleb_37[-2] == "JUMP_FORWARD"
            ):
                node.kind = "testfalse"
                pass
            pass
        self.default(node)
        return

    self.n_testtrue = n_testtrue
