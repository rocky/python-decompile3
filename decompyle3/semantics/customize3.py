#  Copyright (c) 2018-2020 by Rocky Bernstein
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

from decompyle3.scanner import Code
from decompyle3.semantics.consts import TABLE_DIRECT

from xdis.code import iscode
from decompyle3.semantics.customize37 import customize_for_version37
from decompyle3.semantics.customize38 import customize_for_version38


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
            "tf_tryelsestmtc3": ( '%c%-%c%|else:\n%+%c', 1, 3, 5 ),
            "store_locals": ("%|# inspect.currentframe().f_locals = __locals__\n",),
             "with":      ("%|with %c:\n%+%c%-", 0, 3),
            "withasstmt": ("%|with %c as %c:\n%+%c%-", 0, 2, 3),
        }
    )

    assert version >= 3.7

    # In 2.5+ and 3.0+ "except" handlers and the "finally" can appear in one
    # "try" statement. So the below has the effect of combining the
    # "tryfinally" with statement with the "try_except" statement.
    # FIXME: something doesn't smell right, since the semantics
    # are different. See test_fileio.py for an example that shows this.
    def tryfinallystmt(node):
        suite_stmts = node[1][0]
        if len(suite_stmts) == 1 and suite_stmts[0] == 'stmt':
            stmt = suite_stmts[0]
            try_something = stmt[0]
            if try_something == "try_except":
                try_something.kind = "tf_try_except"
            if try_something.kind.startswith("tryelsestmt"):
                if try_something == "c_tryelsestmt":
                    try_something.kind = 'tf_tryelsestmtc3'
                else:
                    try_something.kind = 'tf_tryelsestmt'
        self.default(node)
    self.n_tryfinallystmt = tryfinallystmt

    def listcomp_closure3(node):
        """List comprehensions in Python 3 when handled as a closure.
        See if we can combine code.
        """
        p = self.prec
        self.prec = 27

        code = Code(node[1].attr, self.scanner, self.currentclass)
        ast = self.build_ast(code._tokens, code._customize)
        self.customize(code._customize)

        # skip over: sstmt, stmt, return, ret_expr
        # and other singleton derivations
        while len(ast) == 1 or (
            ast in ("sstmt", "return") and ast[-1] in ("RETURN_LAST", "RETURN_VALUE")
        ):
            self.prec = 100
            ast = ast[0]

        n = ast[1]

        # collections is the name of the expression(s) we are iterating over
        collections = [node[-3]]
        list_ifs = []

        if self.version == 3.0 and n != "list_iter":
            # FIXME 3.0 is a snowflake here. We need
            # special code for this. Not sure if this is totally
            # correct.
            stores = [ast[3]]
            assert ast[4] == "comp_iter"
            n = ast[4]
            # Find the list comprehension body. It is the inner-most
            # node that is not comp_.. .
            while n == "comp_iter":
                if n[0] == "comp_for":
                    n = n[0]
                    stores.append(n[2])
                    n = n[3]
                elif n[0] in ("comp_if", "comp_if_not"):
                    n = n[0]
                    # FIXME: just a guess
                    if n[0].kind == "expr":
                        list_ifs.append(n)
                    else:
                        list_ifs.append([1])
                    n = n[2]
                    pass
                else:
                    break
                pass

            # Skip over n[0] which is something like: _[1]
            self.preorder(n[1])

        else:
            assert n == "list_iter"
            stores = []
            # Find the list comprehension body. It is the inner-most
            # node that is not list_.. .
            while n == "list_iter":
                n = n[0]  # recurse one step
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
                elif n in ("list_if", "list_if_not"):
                    # FIXME: just a guess
                    if n[0].kind == "expr":
                        list_ifs.append(n)
                    else:
                        list_ifs.append([1])
                    n = n[-1]
                    pass
                elif n == "list_if37":
                    list_ifs.append(n)
                    n = n[-1]
                    pass
                pass

            assert n == "lc_body", ast
            self.preorder(n[0])

        # FIXME: add indentation around "for"'s and "in"'s
        for i, store in enumerate(stores):
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
                (1, "suite_stmts_opt"),
                (3, "except_handler"),
                (5, "else_suitec"),
            ),
            "LOAD_CLASSDEREF": ("%{pattr}",),
        }
    )

    TABLE_DIRECT.update({"LOAD_CLASSDEREF": ("%{pattr}",)})

    if version >= 3.7:
        customize_for_version37(self, version)
        if version >= 3.8:
            customize_for_version38(self, version)
            pass  # version >= 3.8
        pass  # 3.7
    return
