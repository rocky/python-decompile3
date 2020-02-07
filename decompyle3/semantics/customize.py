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

"""Isolate Python version-specific semantic actions here.
"""

from decompyle3.semantics.consts import PRECEDENCE, TABLE_R, TABLE_DIRECT

from decompyle3.parsers.treenode import SyntaxTree
from decompyle3.scanners.tok import Token


def customize_for_version(self, is_pypy, version):
    if is_pypy:
        ########################
        # PyPy changes
        #######################
        TABLE_DIRECT.update(
            {
                "assert_pypy": ("%|assert %c\n", 1),
                "assert2_pypy": ("%|assert %c, %c\n", 1, 4),
                "try_except_pypy": ("%|try:\n%+%c%-%c\n\n", 1, 2),
                "tryfinallystmt_pypy": ("%|try:\n%+%c%-%|finally:\n%+%c%-\n\n", 1, 3),
                "assign3_pypy": ("%|%c, %c, %c = %c, %c, %c\n", 5, 4, 3, 0, 1, 2),
                "assign2_pypy": ("%|%c, %c = %c, %c\n", 3, 2, 0, 1),
            }
        )
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

    if version >= 3.2:
        TABLE_DIRECT.update(
            {"del_deref_stmt": ("%|del %c\n", 0), "DELETE_DEREF": ("%{pattr}", 0),}
        )
    from decompyle3.semantics.customize3 import customize_for_version3

    customize_for_version3(self, version)

    return
