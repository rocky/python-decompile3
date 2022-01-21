#  Copyright (c) 2020 Rocky Bernstein
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


def lastc_stmt(
    self, lhs: str, n: int, rule, ast, tokens: list, first: int, last: int
) -> bool:
    # A lastc_stmt really has to be the last thing in a block,
    # a statement that doesn't fall through to the next instruction, or
    # in the case of "POP_BLOCK" is about to end.
    # Otherwise this kind of stmt should flow through to the next.
    # However that larger, set of stmts could be a lastc_stmt, but come back
    # here with that larger set of stmts.

    # print("XXX", first, last, rule)
    # for t in range(first, last): print(tokens[t])
    # print("="*40)

    if tokens[last] == "COME_FROM":
        last -= 1

    # FIXME: use instruction properties.
    return tokens[last] not in (
        "BREAK_LOOP",
        "COME_FROM_LOOP",
        "CONTINUE",
        "JUMP_LOOP",
        "POP_BLOCK",
        "RETURN_VALUE",
    )
