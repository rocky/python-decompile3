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

def ifstmt(
    self, lhs: str, n: int, rule, ast, tokens: list, first: int, last: int
) -> bool:
    # if lhs == "ifstmtc":
    #     if last == n:
    #         last -= 1
    #         pass
    #     if tokens[last].attr and isinstance(tokens[last].attr, int):
    #         if tokens[first].offset >= tokens[last].attr:
    #             return True
    #     pass

    # Test that the outermost COME_FROM, if it exists, must be *somewhere*
    # in the range of the if stmt.
    ltm1 = tokens[last-1]
    if ltm1 == "COME_FROM" and ltm1.attr < tokens[first].off2int():
        return True

    # Make sure jumps don't extend beyond the end of the if statement.
    last_offset = tokens[last].off2int()
    for i in range(first, last):
        t = tokens[i]
        # instead of POP_JUMP_IF, should we use op attributes?
        if t.kind in ("POP_JUMP_IF_FALSE", "POP_JUMP_IF_TRUE"):
            pjif_target = t.attr
            if pjif_target > last_offset:
                # In come cases, where we have long bytecode, a
                # "POP_JUMP_IF_TRUE/FALSE" offset might be too
                # large for the instruction; so instead it
                # jumps to a JUMP_FORWARD. Allow that here.
                if tokens[last] == "JUMP_FORWARD":
                    return tokens[last].attr != pjif_target
                return True
            elif lhs == "ifstmtc" and tokens[first].off2int() > pjif_target:
                # A conditional JUMP to the loop is expected for "ifstmtc"
                return False
            pass
        pass
    pass

    if not ast:
        return False

    testexpr = ast[0]

    if (last + 1) < n and tokens[last + 1] == "COME_FROM_LOOP":
        # iflastsmtl jumped outside of loop. No good.
        return True

    if testexpr[0] in ("testtrue", "testfalse"):
        test = testexpr[0]
        if len(test) > 1 and test[1].kind.startswith("POP_JUMP_IF_"):
            jump_target = test[1].attr
            if (
                tokens[first].off2int(prefer_last=True)
                <= jump_target
                < tokens[last].off2int(prefer_last=False)
            ):
                return True
            # jump_target less than tokens[first] is okay - is to a loop
            # jump_target equal tokens[last] is also okay: normal non-optimized non-loop jump
            if jump_target > tokens[last].off2int():
                # One more weird case to look out for
                #   if c1:
                #      if c2:  # Jumps around the *outer* "else"
                #       ...
                #   else:
                if jump_target == tokens[last - 1].attr:
                    return False
                if last < n and tokens[last].kind.startswith("JUMP"):
                    return False
                return True

        pass

    return False
