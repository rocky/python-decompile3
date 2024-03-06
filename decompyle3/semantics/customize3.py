#  Copyright (c) 2018-2022 by Rocky Bernstein
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

"""Isolate Python 3 version-specific semantic actions here.
"""

from xdis import co_flags_is_async, iscode

from decompyle3.scanner import Code
from decompyle3.semantics.consts import TABLE_DIRECT
from decompyle3.semantics.customize37 import customize_for_version37
from decompyle3.semantics.customize38 import customize_for_version38
from decompyle3.semantics.helper import is_lambda_mode


def customize_for_version3(self, version):
    TABLE_DIRECT.update(
        {
            "comp_for": (" for %c in %c", (2, "store"), (0, "expr")),
            "if_exp_not": (
                "%c if not %c else %c",
                (2, "expr"),
                (0, "expr"),
                (4, "expr"),
            ),
            "except_cond2": ("%|except %c as %c:\n", (1, "expr"), (5, "store")),
            "function_def_annotate": ("\n\n%|def %c%c\n", -1, 0),
            # When a generator is a single parameter of a function,
            # it doesn't need the surrounding parenethesis.
            "call_generator": ("%c%P", 0, (1, -1, ", ", 100)),
            "importmultiple": ("%|import %c%c\n", 2, 3),
            "import_cont": (", %c", 2),
            "raise_stmt2": ("%|raise %c from %c\n", 0, 1),
            "tf_tryelsestmtc3": ("%c%-%c%|else:\n%+%c", 1, 3, 5),
            "store_locals": ("%|# inspect.currentframe().f_locals = __locals__\n",),
            "with": ("%|with %c:\n%+%c%-", 0, 3),
        }
    )

    assert version >= (3, 7)

    # In 2.5+ and 3.0+ "except" handlers and the "finally" can appear in one
    # "try" statement. So the below has the effect of combining the
    # "tryfinally" with statement with the "try_except" statement.
    # FIXME: something doesn't smell right, since the semantics
    # are different. See test_fileio.py for an example that shows this.
    def n_tryfinallystmt(node):
        suite_stmts = node[1][0]
        if len(suite_stmts) == 1 and suite_stmts[0] == "stmt":
            stmt = suite_stmts[0]
            try_something = stmt[0]
            if try_something == "try_except":
                try_something.kind = "tf_try_except"
            if try_something.kind.startswith("tryelsestmt"):
                if try_something == "c_tryelsestmt":
                    try_something.kind = "tf_tryelsestmtc3"
                else:
                    try_something.kind = "tf_tryelsestmt"
        self.default(node)

    self.n_tryfinallystmt = n_tryfinallystmt

    def listcomp_closure3(node):
        """List comprehensions in Python 3 when handled as a closure.
        See if we can combine code.
        """

        # FIXME: DRY with comprehension_walk_newer
        p = self.prec
        self.prec = 27

        code_obj = node[1].attr
        assert iscode(code_obj), node[1]
        code = Code(code_obj, self.scanner, self.currentclass, self.debug_opts["asm"])

        tree = self.build_ast(
            code._tokens,
            code._customize,
            code,
            is_lambda=is_lambda_mode(self.compile_mode),
        )
        self.customize(code._customize)

        # skip over: sstmt, stmt, return, return_expr
        # and other singleton derivations
        while len(tree) == 1 or (
            tree in ("sstmt", "return", "return_expr_lambda", "lambda_start")
            and tree[-1]
            in ("LAMBDA_MARKER", "RETURN_VALUE_LAMBDA", "RETURN_LAST", "RETURN_VALUE")
        ):
            self.prec = 100
            tree = tree[0]

        n = tree[1]

        # Pick out important parts of the comprehension:
        # * the variables we iterate over: "stores"
        # * the results we accumulate: "n"

        # collections is the name of the expression(s) we are iterating over
        collections = [node[-3]]
        list_ifs = []

        assert n == "list_iter"
        stores = []
        # Find the list comprehension body. It is the inner-most
        # node that is not list_.. .
        while n == "list_iter":

            # recurse one step
            n = n[0]

            if n == "list_for":
                stores.append(n[2])
                n = n[3]
                if n[0] == "list_for":
                    # Dog-paddle down largely singleton reductions
                    # to find the collection (expr)
                    c = n[0][0]
                    if c == "expr":
                        c = c[0]
                    # FIXME: grammar is wonky here? Is this really an attribute?
                    if c == "attribute":
                        c = c[0]
                    collections.append(c)
                    pass
            elif n in ("list_if", "list_if_not", "list_if_or_not"):
                if n[0].kind == "expr":
                    list_ifs.append(n)
                else:
                    list_ifs.append([1])
                n = n[-2] if n[-1] == "come_from_opt" else n[-1]
                pass
            elif n == "list_if37":
                list_ifs.append(n)
                n = n[-1]
                pass
            elif n == "list_afor":
                collections.append(n[0][0])
                n = n[1]
                stores.append(n[1][0])
                n = n[2] if n[2].kind == "list_iter" else n[3]
            pass

        assert n == "lc_body", tree
        self.preorder(n[0])

        # FIXME: add indentation around "for"'s and "in"'s
        n_colls = len(collections)
        for i, store in enumerate(stores):
            if i >= n_colls:
                break
            if collections[i] == "LOAD_DEREF" and co_flags_is_async(code_obj.co_flags):
                self.write(" async")
                pass
            self.write(" for ")
            self.preorder(store)
            self.write(" in ")
            self.preorder(collections[i])
            if i < len(list_ifs):
                self.preorder(list_ifs[i])
                pass
            pass
        self.prec = p

    self.listcomp_closure3 = listcomp_closure3

    TABLE_DIRECT.update(
        {
            "c_tryelsestmt": (
                "%|try:\n%+%c%-%c%|else:\n%+%c%-",
                (1, "c_suite_stmts"),
                (3, "c_except_handler"),
                (5, "else_suitec"),
            ),
            "LOAD_CLASSDEREF": ("%{pattr}",),
        }
    )

    TABLE_DIRECT.update({"LOAD_CLASSDEREF": ("%{pattr}",)})

    if version >= (3, 7):
        customize_for_version37(self, version)
        if version >= (3, 8):
            customize_for_version38(self, version)
            pass  # version >= 3.8
        pass  # 3.7
    return
