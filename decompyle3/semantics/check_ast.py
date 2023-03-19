#  Copyright (c) 2019 Rocky Bernstein
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
Python parse tree checker.

Our rules sometimes give erroneous results. Until we have perfect rules,
This checker will catch mistakes in decompilation we've made.

FIXME idea: extend parsing system to do same kinds of checks or nonterminal
before reduction and don't reduce when there is a problem.
"""


def checker(ast, in_loop: bool, errors) -> None:
    if ast is None:
        return

    in_loop = (
        in_loop
        or ast.kind.startswith("while")
        or ast.kind.startswith("async_for")
        or ast.kind.startswith("for")
    )
    if ast.kind in ("aug_assign1", "aug_assign2") and ast[0][0] == "and":
        text = str(ast)
        error_text = (
            "\n# improper augmented assignment (e.g. +=, *=, ...):\n#\t"
            + "\n# ".join(text.split("\n"))
            + "\n"
        )
        errors.append(error_text)

    for node in ast:
        if not in_loop and node.kind in ("continue", "break"):
            text = str(node)
            error_text = "\n# not in loop:\n#\t" + "\n# ".join(text.split("\n"))
            errors.append(error_text)
        if hasattr(node, "__repr1__"):
            checker(node, in_loop, errors)
