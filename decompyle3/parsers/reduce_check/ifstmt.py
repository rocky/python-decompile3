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

#  Example A: an example where we have weird COME_FROMs
#
#   if a:
#     if b:   # false jumps around outer else
#       raise
#   elif c:
#      a = 2
#   #end is jump to by "if not b" above


def ifstmt(
    self, lhs: str, n: int, rule, tree, tokens: list, first: int, last: int
) -> bool:

    # print("XXX", tokens[first].offset , tokens[last].offset, rule)
    # for t in range(first, last):
    #     print(tokens[t])
    # print("=" * 40)

    if rule == ("ifstmt", ("bool_op", "stmts", "\\e__come_froms")):
        return False

    ltm1_index = last - 1
    while tokens[ltm1_index] == "COME_FROM":
        ltm1_index -= 1
    ltm1 = tokens[ltm1_index]

    first_offset = tokens[first].off2int(prefer_last=False)

    # The below doesn't work for Example A above
    # # Test that the outermost COME_FROM, if it exists, must be *somewhere*
    # # in the range of the if stmt.
    # if ltm1 == "COME_FROM" and ltm1.attr < first_offset:
    #     return True

    if not tree:
        return False

    ifstmts_jump = tree[1]
    if ifstmts_jump.kind.startswith("ifstmts_jump"):
        come_from = ifstmts_jump[0]
        if come_from == "COME_FROM" and come_from.attr < first_offset:
            return True

    testexpr = tree[0]

    test = testexpr[0]

    # We have two grammar rules: ifstmtc and if_not_stmtc
    # which are the same:
    #    xxx  ::= testexprc ifstmts_jumpc _come_froms
    # and these need to be disambiguated
    # When  ifstmts_jumpc goes back to to a loop
    # and testexprc is testtruec, then we have if_not_stmtc.

    if lhs == "ifstmtc" and test == "testtruec" and ifstmts_jump == "ifstmts_jumpc":
        if len(test) > 1:
            return test[1] != "POP_JUMP_IF_FALSE_LOOP"

    if lhs == "if_not_stmtc" and ifstmts_jump == "ifstmts_jumpc":
        if test == "testexpr":
            test = test[0]
        if test in ("testfalsec", "testfalse"):
            return True

        if test in ("testtruec", "testtrue") and ifstmts_jump == "ifstmts_jumpc":
            if test[0] == "expr_pjit":
                test = test[0]
            if len(test) > 1:
                return test[1] == "POP_JUMP_IF_FALSE_LOOP"

    pop_jump_if = None

    if test in ("testexpr", "testexprc"):
        test = test[0]

    pop_jump_if = None
    if test in ("testtrue", "testtruec", "testfalse"):

        if len(test) == 1 and test[0].kind.startswith("expr_pji"):
            pop_jump_if = test[0][1]
        elif len(test) > 1 and test[1].kind.startswith("POP_JUMP_IF_"):
            pop_jump_if = test[1]

        if pop_jump_if:
            jump_target = pop_jump_if.attr
            if last == n:
                last -= 1

            # Get reasonable offset "end if" offset
            endif_offset = ltm1.off2int(prefer_last=True)
            if endif_offset == -1:
                endif_offset = tokens[last - 2].off2int(prefer_last=True)

            if first_offset <= jump_target < endif_offset:
                if rule[1] == ("testexpr", "stmts", "come_froms"):
                    come_froms = tree[2]

                    if hasattr(come_froms, "first_child"):
                        come_from_offset = come_froms.first_child()
                    else:
                        assert come_froms.kind.startswith("COME_FROM")
                        come_from_offset = come_froms.off2int()
                    return jump_target != come_from_offset
                # FIXME: investigate why this happens for "if"s with EXTENDED_ARG POP_JUMP_IF_FALSE.
                # An example is decompyle3/semantics/transform.py n_ifelsestmt.py
                elif rule[1][-1] == "\\e__come_froms":
                    return True
                pass

            endif_inst_index = self.offset2inst_index[ltm1.off2int(prefer_last=False)]

            # FIXME: RAISE_VARARGS is an instance of a no-follow instruction.
            # Should this be generalized? For example for RETURN ?
            if ltm1.kind.startswith("RAISE_VARARGS"):
                endif_inst_index += 2

            if endif_inst_index + 1 == len(self.insts):
                return False
            endif_next_inst = self.insts[endif_inst_index + 1]

            # jump_target equal tokens[last] is also okay: normal non-optimized non-loop jump
            if jump_target > endif_next_inst.offset:
                # test for Example A where "if b" jumps around the outer "else"
                if jump_target == tokens[last - 1].attr:
                    return False
                if last < n and tokens[last].kind.startswith("JUMP"):
                    # Distinguish code like:
                    #
                    #   if a and not b:  # there are two jumps to "else" here
                    #     real = 2       # there is a jump around the else here
                    #  else:
                    #     real = 3
                    #
                    # and don't confuse with:
                    #
                    #   if a:
                    #     if not b:      # the test below excludes this inner "if"
                    #        real = 2
                    #   real = 3
                    # which is wrong
                    if (
                        first > 0
                        and tokens[first - 1].kind.startswith("POP_JUMP_IF_")
                        and tokens[first - 1].attr == jump_target
                    ):
                        return True
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
                    before_come_from = self.insts[
                        self.offset2inst_index[endif_offset] - 1
                    ]
                    # FIXME: When xdis next changes, this will be a field in the instruction
                    no_follow = before_come_from.opcode in self.opc.nofollow
                    return not (before_come_from.is_jump() or no_follow)
            elif pop_jump_if == "POP_JUMP_IF_TRUE":
                # Make sure pop_jump_if doesn't jump inside the "then" part of the "if"
                # print("WOOT", pop_jump_if.attr - endif_offset)
                # We leave some slop for endif_offset being one instruction behind.

                return not ((pop_jump_if.attr - endif_offset) in (0, 2))
        pass

    # If there is a final COME_FROM and that test jumps to that, this is a strong
    # indication that this is ok, so we'll skip jumps jumping too far test.
    if (
        pop_jump_if is not None
        and ltm1 == "COME_FROM"
        and ltm1.attr == pop_jump_if.off2int()
    ):
        return False

    # Make sure jumps don't extend beyond the end of the if statement.
    # This is done after the weird stuff above. There is a problem with the
    # below is that it suffers from example A the "if b" jumping around
    # the outer else. So we do this after all of the above and
    # rely on the above COME_FROM test.

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

    # If the "if_stmt" includes a COME_FROM from before the beginning of the "if", then
    # no good. If the "if stmt" covers the non-COME_FROM instructions, there will have
    # been a prior reduction that doesn't include the last COME_FROM.
    if ltm1 == "COME_FROM":
        return ltm1.attr < first_offset
    elif tokens[last] == "COME_FROM":
        return tokens[last].attr < first_offset

    return False
