#  Copyright (c) 2018-2021 by Rocky Bernstein
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

"""Isolate Python version-specific semantic actions here.
"""

from decompyle3.semantics.consts import INDENT_PER_LEVEL, PRECEDENCE, TABLE_DIRECT
from decompyle3.semantics.helper import flatten_list


def customize_for_version(self, is_pypy, version):
    if is_pypy:
        ########################
        # PyPy changes
        #######################
        TABLE_DIRECT.update(
            {
                "assert": ("%|assert %c\n", 0),
                "assert_pypy": ("%|assert %c\n", 1),
                "assert2_pypy": ("%|assert %c, %c\n", 1, 4),
                "try_except_pypy": ("%|try:\n%+%c%-%c\n\n", 1, 2),
                "tryfinallystmt_pypy": ("%|try:\n%+%c%-%|finally:\n%+%c%-\n\n", 1, 3),
                "assign3_pypy": ("%|%c, %c, %c = %c, %c, %c\n", 5, 4, 3, 0, 1, 2),
                "assign2_pypy": ("%|%c, %c = %c, %c\n", 3, 2, 0, 1),
            }
        )
        if version[:2] == (3, 7):

            def n_call_kw_pypy37(node):
                self.template_engine(("%p(", (0, 100)), node)
                assert node[-1] == "CALL_METHOD_KW"
                pypy_kw_keys = node[-2]
                assert pypy_kw_keys == "pypy_kw_keys"

                flat_elems = flatten_list(node[1:-2])
                # FIXME zip pypy_kw_keys and elems

                self.indent_more(INDENT_PER_LEVEL)
                sep = ""

                n = len(flat_elems)
                kw_keys_tuple = pypy_kw_keys[0].attr
                assert n == len(kw_keys_tuple)
                for i in range(n):
                    elem = flat_elems[i]
                    assert elem == "expr"
                    line_number = self.line_number
                    value = self.traverse(elem)
                    if line_number != self.line_number:
                        sep += "\n" + self.indent + INDENT_PER_LEVEL[:-1]
                        pass
                    self.write(sep)
                    self.write(f"{kw_keys_tuple[i]}={value}")
                    sep = ", "
                    pass

                self.write(")")
                self.prune()

            self.n_call_kw_pypy37 = n_call_kw_pypy37

    else:
        ########################
        # Without PyPy
        #######################
        TABLE_DIRECT.update(
            {
                # "assert" and "assert_expr" are added via transform rules.
                "assert": ("%|assert %c\n", 0),
                "assert2": ("%|assert %c, %c\n", 0, 3),
                # Created only via transformation
                "assertnot": ("%|assert not %p\n", (0, PRECEDENCE["unary_not"])),
                "assert2not": (
                    "%|assert not %p, %c\n",
                    (0, PRECEDENCE["unary_not"]),
                    3,
                ),
                "assign2": ("%|%c, %c = %c, %c\n", 3, 4, 0, 1),
                "assign3": ("%|%c, %c, %c = %c, %c, %c\n", 5, 6, 7, 0, 1, 2),
                "try_except": ("%|try:\n%+%c%-%c\n\n", 1, 3),
            }
        )

    if version >= (3, 2):
        TABLE_DIRECT.update(
            {"del_deref_stmt": ("%|del %c\n", 0), "DELETE_DEREF": ("%{pattr}", 0),}
        )
    from decompyle3.semantics.customize3 import customize_for_version3

    customize_for_version3(self, version)

    return
