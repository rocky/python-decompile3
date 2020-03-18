#  Copyright (c) 2020 Rocky Bernstein
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

def list_if_not(
    self, lhs: str, n: int, rule, ast, tokens: list, first: int, last: int
) -> bool:
    assert rule[1][:-1] == ("expr", "POP_JUMP_IF_TRUE", "list_iter")
    # The jump should not be somewhere inside the list_if_not
    return tokens[first].off2int(prefer_last=False) < ast[1].attr < tokens[last].off2int(prefer_last=True)
