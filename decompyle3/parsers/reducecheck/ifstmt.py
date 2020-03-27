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

    # print("XXX", first, last, rule)
    # for t in range(first, last):
    #     print(tokens[t])
    # print("=" * 40)

    ltm1 = tokens[last - 1]
    first_offset = tokens[first].off2int(prefer_last=False)

    # Test that the outermost COME_FROM, if it exists, must be *somewhere*
    # in the range of the if stmt.
    if ltm1 == "COME_FROM" and ltm1.attr < first_offset:
        return True

    # Make sure jumps don't extend beyond the end of the if statement.
    last_offset = tokens[last].off2int()
    for i in range(first, last):
        t = tokens[i]
        # instead of POP_JUMP_IF, should we use op attributes?
        if t.kind.startswith("POP_JUMP_IF_"):
            pjif_target = t.attr
            if pjif_target > last_offset:
                # In some cases, where we have long bytecode, a
                # "POP_JUMP_IF_TRUE/FALSE" offset might be too
                # large for the instruction; so instead it
                # jumps to a JUMP_FORWARD. Allow that here.
                if tokens[last] == "JUMP_FORWARD":
                    return tokens[last].attr != pjif_target
                return True
            # elif lhs == "ifstmtc" and tokens[first].off2int() > pjif_target:
            #     # A conditional JUMP to the loop is expected for "ifstmtc"
            #     return True
            pass
        pass

    if not ast:
        return False

    testexpr = ast[0]

    test = testexpr[0]
    if test in ("testexpr", "testexprc"):
        test = test[0]

    if test in ("testtrue", "testtruec", "testfalse"):

        if len(test) > 1 and test[1].kind.startswith("POP_JUMP_IF_"):
            pop_jump_if = test[1]
            jump_target = pop_jump_if.attr
            if last == n:
                last -= 1

            # Get reasonable offset end_if offset
            endif_offset = ltm1.off2int(prefer_last=False)
            if endif_offset == -1:
                endif_offset = tokens[last - 2].off2int(prefer_last=False)

            if first_offset <= jump_target < endif_offset:
                # FIXME: investigate why this happens for "if"s with EXTENDED_ARG POP_JUMP_IF_FALSE.
                # An example is decompyle3/semantics/transform.py n_ifelsestmt.py
                if not (
                        jump_target != endif_offset or
                        rule == ('ifstmt', ('testexpr', 'stmts', 'come_froms'))):
                    return True

            # jump_target equal tokens[last] is also okay: normal non-optimized non-loop jump
            # HACK Alert: +2 refers to instruction offset after endif
            if jump_target > endif_offset + 2:
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
            elif jump_target < first_offset:
                # jump_target less than tokens[first] is okay - is to a loop
                assert test == "testtruec"  # and lhs == "ifsmtc"
                # Since the "if" test is backwards, there shouldn't
                # be a "COME_FROM", but should be some sort of
                # instruction that does "not' fall through, like a jump
                # return, or raise.
                if ltm1 == "COME_FROM":
                    before_come_from = self.insts[self.offset2inst_index[endif_offset]-1]
                    # FIXME: When xdis next changes, this will be a field in the instruction
                    no_follow = before_come_from.opcode in self.opc.nofollow
                    return not (before_come_from.is_jump() or no_follow)

        pass

    return False
