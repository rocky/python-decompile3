#  Copyright (c) 2020-2022 Rocky Bernstein
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
    self, lhs: str, n: int, rule, tree, tokens: list, first: int, last: int
) -> bool:
    assert rule[1][:-1] == ("expr", "list_if_not_end", "list_iter")
    pop_jump_if = tree[1][0][0]
    assert pop_jump_if.kind.startswith("POP_JUMP_IF_TRUE")
    # The jump should not be somewhere inside the list_if_not,
    # unless the list_iter is another "list_if"
    if (
        tokens[first].off2int(prefer_last=False)
        < pop_jump_if.attr
        < tokens[last].off2int(prefer_last=True)
    ):
        list_iter = tree[2]
        assert list_iter == "list_iter"
        return list_iter[0] != "list_if"
    return False
