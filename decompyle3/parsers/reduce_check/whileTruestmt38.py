#  Copyright (c) 2022 Rocky Bernstein
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


def whileTruestmt38_check(
    self, lhs: str, n: int, rule, tree, tokens: list, first: int, last: int
) -> bool:
    # When we are missing a COME_FROM_LOOP, the
    # "while" statement is nested inside an if/else
    # so after the POP_BLOCK we have a JUMP_FORWARD which forms the "else" portion of the "if"
    # Check this.
    # print("XXX", first, last, rule)
    # for t in range(first, last): print(tokens[t])
    # print("="*40)

    if tokens[last] != "COME_FROM" and tokens[last - 1] == "COME_FROM":
        last -= 1
    if tokens[last - 1].kind.startswith("RAISE_VARARGS"):
        return True
    while tokens[last] == "COME_FROM":
        last -= 1
    if rule[-1][-1] == "\\e__come_froms" and rule[-1][-2] == "JUMP_LOOP":
        while tokens[last] != "JUMP_LOOP":
            last -= 1
    jump_loop = tokens[last]
    if jump_loop == "JUMP_LOOP":

        jump_target = jump_loop.attr
        if jump_target < tokens[first].off2int(prefer_last=False):
            return True

        c_stmts = tree[1]
        if c_stmts == "c_stmts":
            c_stmts_offset = c_stmts.first_child().off2int()
            return c_stmts_offset != jump_target

    return False
