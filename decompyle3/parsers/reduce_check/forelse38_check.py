#  Copyright (c) 2023 Rocky Bernstein
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

from decompyle3.scanners.tok import off2int


def forelse38_invalid(
    self, lhs: str, n: int, rule, tree, tokens: list, first: int, last: int
) -> bool:
    """The only difference between a "forelse" and and a "for" is that
    that the "come_from" location contains something other than
    for_iter.
    """

    come_froms = tree[5]
    # from trepan.api import debug; debug()
    if come_froms != "_come_froms" or come_froms[0] != "_come_froms":
        return False

    return len(come_froms) == 2 and come_froms[1] == "COME_FROM"
