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


def forelse38_invalid(
    self, lhs: str, n: int, rule, tree, tokens: list, first: int, last: int
) -> bool:
    """The only difference between a "forelse" and and a "for" is that
    that the "come_from" location contains something other than
    for_iter.
    """

    saw_break = False
    saw_break_to_last = False
    last_offset = tokens[last].off2int()

    # for i in range(first, last):
    #     print(tokens[i])

    else_start = None
    for node in tree:
        if node.kind.startswith("else"):
            else_start = node.first_child().off2int()
    assert else_start is not None

    for i in range(first, last):
        t = tokens[i]
        if t.off2int() >= else_start:
            break
        if t == "BREAK_LOOP":
            if else_start <= t.attr < last_offset:
                # We should not be jumping into the "else" part.
                return True
            saw_break = True
            saw_break_to_last = t.attr == last_offset
            # if saw_break_to_last:
            #     from trepan.api import debug; debug()
        if t.kind == "JUMP_FORWARD":
            # We should be jumping to the "else" part.
            if not t.attr == else_start:
                return True

    # If we haven't seen a BREAK_LOOP, then
    # "for/else" and "for" are the same. But here
    # we should prefer the simpler "for"
    if saw_break:
        return not saw_break_to_last
    return True
