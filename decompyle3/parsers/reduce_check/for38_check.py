#  Copyright (c) 2020, 2022-2024 Rocky Bernstein
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


def for38_invalid(
    self, lhs: str, n: int, rule, tree, tokens: list, first: int, last: int
) -> bool:
    """The only difference between a "for" and a "for else" is that
    jumps within the "for" never go past the "FOR_ITER" offset.
    """

    first_offset = tokens[first].off2int(prefer_last=False)
    last_offset = tokens[last].off2int(prefer_last=False)
    if last_offset == -1:
        last_offset = tokens[last - 1].off2int(prefer_last=False)

    start = self.offset2inst_index[first_offset]
    end = off2int(self.offset2inst_index[last_offset], prefer_last=True)

    # In the loop below, we expect the first "FOR_ITER" to
    # be before any jumps that go to the end of it (in the case of "for")
    # or beyond it (in the case of "for else").

    for_body_end_offset = None
    for i in range(start, end):
        inst = self.insts[i]

        # Hack alert for magic number 2's below: in Python 3.8+ instructions are 2 bytes
        # inst.argval - 2 is the offset of the instruction *before* inst.argval and
        # +2 for the instruction that follows.

        if not for_body_end_offset and inst.opname == "FOR_ITER":
            # There can be some slop in "last" as to where the body ends. If the rule
            # ends in "JUMP_LOOP", then "last" doesn't need adjusting.
            for_body_end_offset = (
                inst.argval if rule[1][-1] == "JUMP_LOOP" else inst.argval - 2
            )
            if self.insts[end].has_extended_arg:
                last_offset += 2
            if last_offset < for_body_end_offset:
                # "for" body isn't big enough
                return True
            continue
        if (
            for_body_end_offset
            and inst.is_jump()
            and inst.argval > for_body_end_offset + 2
        ):
            # Another weird case.
            # Guard against misclassified things like:
            #   if a:
            #     for n in l:
            #       if b: break # jumps past "else" which is after the end of the "for"
            #       eird case.
            # Guard against misclassified things like:
            #   if a:
            #     for n in l:
            #       if b: break # jumps past "else" which is after the end of the "for"
            #       elif c:
            #         r = 2
            #   else:
            #        r = 3
            # The way we distinguish this is to check if the instruction after the body end
            # starts with a jump, the start of the encompassing if/else.
            # The "else" part of a "for/else" never starts with a jump.
            body_end_next_inst = self.insts[
                self.offset2inst_index[for_body_end_offset + 2]
            ]
            return not body_end_next_inst.is_jump()
    return False
