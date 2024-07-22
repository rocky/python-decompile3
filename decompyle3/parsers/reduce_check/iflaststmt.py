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

from decompyle3.scanners.tok import Token


def iflaststmt(
    self, lhs: str, n: int, rule, tree, tokens: list, first: int, last: int
) -> bool:
    testexpr = tree[0]
    rhs = rule[1]

    # print("XXX", first, last, rule)
    # for t in range(first, last): print(tokens[t])
    # print("="*40)

    # FIXME: should this be done in the caller?
    if tokens[last] == "RETURN_LAST":
        last -= 1

    # If there is a fall-through it shouldn't be somewhere
    # inside iflaststmt, since the point of this is to handle
    # if statements that *don't* fall though.
    if tokens[last] == "COME_FROM":
        come_from_offset = tokens[last].attr
        if tokens[first].off2int() <= come_from_offset <= tokens[last].off2int():
            return True

    if rhs[0:2] in (
        ("testexpr", "stmts"),
        ("testexpr", "c_stmts"),
        ("testexprc", "c_stmts"),
    ):

        # "stmts" (end of then) should not end in a fallthrough instruction
        # other wise this is just a plain ol' stmt.
        ltm1 = tokens[last - 1]
        if ltm1 == "COME_FROM":
            return True
        then_end = self.off2inst(ltm1)

        # FIXME: fallthrough should be an xdis thing. Until then...
        if then_end.opcode not in self.opc.nofollow and tokens[last] != "JUMP_LOOP":
            return True

        # If there is a trailing if-jump (forward) at the end of "testexp", it should
        # to the end of "stmts".

        # If there was backward jump, the LHS would be "iflaststmtc".
        # Note that there might not be a COME_FROM before "stmts" because there can be a fall
        # through to it.
        stmt_offset = tree[1].first_child().off2int(prefer_last=False)
        inst_offset = self.offset2inst_index[stmt_offset]

        test_expr_offset = tree[0].first_child().off2int(prefer_last=False)
        test_inst_offset = self.offset2inst_index[test_expr_offset]

        last_offset = tokens[last].off2int(prefer_last=False)

        # Make sure there are *forward* jumps outside offset range of this construct.
        # This helps distinguish:
        #     while True:
        #        if testexpr
        # from:
        #     while testexpr
        for i in range(test_inst_offset, inst_offset):
            inst = self.insts[i]
            if inst.is_jump() and inst.argval > last_offset:
                return True

        testexpr_last_inst = self.insts[inst_offset - 1]
        if testexpr_last_inst.is_jump():
            target_offset = testexpr_last_inst.argval
            if target_offset != last_offset:
                if target_offset < last_offset:
                    # Look for this kind of situation from: iflaststmtc ::= testexprc c_stmts
                    #
                    # L.  13        78  LOAD_NAME                ncols
                    #               80  POP_JUMP_IF_FALSE_LOOP    40  'to 40'
                    #
                    # L.  14        82  POP_TOP
                    #               84  CONTINUE             20  'to 20'
                    #                   ^^^^^^^^^
                    #
                    #  L.  15        86  JUMP_LOOP            40  'to 40'
                    #                    COME_FROM ...
                    #                    ^^^ last
                    return tokens[last - 2] != "CONTINUE"

                # There is still this weird case:
                # if a:
                #   if b:
                #     x += 3
                #     # jumps to same place as "if a then.." end jump.
                # else:
                #    ...
                # we are going to hack this by looking for another jump to the same target. Sigh.
                i = inst_offset
                inst = self.insts[i]
                while inst.offset < target_offset:
                    if inst.is_jump() and inst.argval == target_offset:
                        return False
                    i += 1
                    inst = self.insts[i]
                    pass
                last_index = self.offset2inst_index[last_offset]
                last_inst = self.insts[last_index]
                # Jumping beyond last_offset is okay since this may be the
                # inner "if" jumping around the "else" situation above.
                if last_inst.is_jump():
                    return target_offset == last_offset
                else:
                    # A fallthrough can't jump *beyond* the end in the nested
                    # "if" around and outer "else"
                    return True
            pass
        pass

    if testexpr[0] == "testexpr":
        testexpr = testexpr[0]
    if testexpr[0] in ("testtrue", "testtruec", "testfalse", "testfalsec"):

        if_condition = testexpr[0]
        if_condition_len = len(if_condition)
        if_bool = if_condition[0]
        if (
            if_condition_len == 1
            and if_bool in ("nand", "and")
            and rhs == ("testexpr", "stmts")
        ):
            # (n)and rules have precedence
            return True
        elif if_bool == "not_or":
            then_end = if_bool[-1]
            if isinstance(then_end, Token):
                then_end_come_from = then_end
            else:
                then_end_come_from = if_bool[-2].last_child()

            # If there jump location is right after then end of this rule, then we have
            # an "and", not a "not_or"

            if (
                then_end_come_from == "POP_JUMP_IF_FALSE"
                and then_end_come_from.attr == tokens[last].off2int()
            ):
                return True
            pass

        if if_condition_len > 1 and if_condition[1].kind.startswith("POP_JUMP_IF_"):
            if last == n:
                last -= 1
            jump_target = if_condition[1].attr
            first_offset = tokens[first].off2int()
            if first_offset <= jump_target < tokens[last].off2int():
                return True
            # jump_target less than tokens[first] is okay - is to a loop
            # jump_target equal tokens[last] is also okay: normal non-optimized non-loop jump

            if (last + 1) < n:
                if tokens[last - 1] == "JUMP_LOOP":
                    if jump_target > first_offset:
                        # The end of the iflaststmt if test jumps backward to a loop
                        # but the false branch of the "if" doesn't also jump back.
                        # No good. This is probably an if/else instead.
                        return True
                    pass
                elif (
                    tokens[last + 1] == "COME_FROM_LOOP"
                    and tokens[last] != "BREAK_LOOP"
                ):
                    # iflastsmtc is not at the end of a loop, but jumped outside of loop. No good.
                    # FIXME: check that tokens[last] == "POP_BLOCK"? Or allow for it not to appear?
                    return True

            # If the instruction before "first" is a "POP_JUMP_IF_FALSE" which goes
            # to the same target as jump_target, then this not nested "if .. if .."
            # but rather "if ... and ..."
            if first > 0 and tokens[first - 1] == "POP_JUMP_IF_FALSE":
                return tokens[first - 1].attr == jump_target

            if jump_target > tokens[last].off2int():
                if jump_target == tokens[last - 1].attr:
                    # if c1 [jump] jumps exactly the end of the iflaststmt...
                    return False
                pass
            pass
        pass
    return False
