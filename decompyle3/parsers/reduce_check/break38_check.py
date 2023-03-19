#  Copyright (c) 2020, 2022 Rocky Bernstein
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


def break_invalid(
    self, lhs: str, n: int, rule, ast, tokens: list, first: int, last: int
) -> bool:

    if rule[1] != ("POP_EXCEPT", "JUMP_FORWARD"):
        return False

    # Look for a JUMP_LOOP instruction either after
    # the end of this rule or before the place where
    # we JUMP_FORWARD to
    if last + 1 < n and tokens[last + 1] == "JUMP_LOOP":
        return False

    # FIXME: put jump_loop classification in a subroutine. Preferably in xdis.
    jump_target_prev = self.insts[self.offset2inst_index[tokens[first + 1].attr] - 1]
    is_jump_loop = (
        jump_target_prev.is_jump() and jump_target_prev.arg < jump_target_prev.offset
    )
    return not is_jump_loop
