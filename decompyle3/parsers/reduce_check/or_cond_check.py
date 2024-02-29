#  Copyright (c) 2020, 2023-2024 Rocky Bernstein
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


def or_cond_check_invalid(
    self, lhs: str, n: int, rule, tree, tokens: list, first: int, last: int
) -> bool:
    if rule == ("or_cond", ("or_parts", "expr_pjif", "come_froms")):
        if tokens[last - 1] == "COME_FROM":
            return tokens[last - 1].attr < tokens[first].off2int()
    last_offset = tokens[last].off2int()
    for i in range(first, last):
        t = tokens[i]
        if t.kind.startswith("POP_JUMP_IF"):
            if t.attr > last_offset:
                return True
    return False
