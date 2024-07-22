#  Copyright (c) 2020, 2022-2023 Rocky Bernstein
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


# When we use dominators, presumbaly this will be a lto cleaner
def ifelsestmt(
    self, lhs: str, n: int, rule, tree, tokens: list, first: int, last: int
) -> bool:

    if (last + 1) < n and tokens[last + 1] == "COME_FROM_LOOP":
        # ifelsestmt jumped outside of loop. No good.
        return True

    # print("XXX", first, last, rule)
    # for t in range(first, last): print(tokens[t])
    # print("="*40)

    first_offset = tokens[first].off2int()
    last_offset = tokens[last].off2int(prefer_last=False)

    # FIXME: It is conceivable the below could be handled strictly in the grammar.
    # If we have an optional else, then we *must* have a COME_FROM for it.
    # Otherwise this is fine as an "if" without the "else"

    if rule[1][2] == "jf_cfs":
        jf_cfs = tree[2]
        jump = jf_cfs[0]
        # The jf_cfs should jump to the end of the ifelse, and not beyond it.
        # Think about: should we also check that it isn't to the
        # *interior* of the "else" part?
        jump = jf_cfs[0]
        if jump == "JUMP_FORWARD" and jump.attr > last_offset:
            # There is one situation where jf_cfs does not jump to the end of ifelse,
            # and that when this is inside *another* ifelse:
            # if x:
            #   if y:
            #     ...
            #   else:
            #     jumps to the end of the *enclosing* ifelse
            # else
            # ...
            #
            # We can detect this because there is a JUMP_FORWARD a the end of the ifelese
            # that also jumps to the same location
            if not (tokens[last] == "JUMP_FORWARD" and tokens[last].attr == jump.attr):
                return True

    if rule[1][2:4] == ("jf_cfs", "\\e_else_suite_opt"):
        come_froms = jf_cfs[1]
        if isinstance(come_froms, Token):
            come_from_target = come_froms.attr
        else:
            if len(come_froms) == 0:
                # We are seeing in optional else's:
                #   XX       JUMP_FORWARD         XX+2
                #   XX+2_00  COME_FROM            XX
                # and these aren't caught by our "if/then" rules
                return tokens[last].off2int() != jf_cfs[0].attr
            come_from_target = come_froms[-1].attr

        if come_from_target < first_offset:
            return True

    # Make sure all the offsets from the "COME_FROMs" at the
    # end of the "if" come from somewhere inside the "if".
    # Since the come_froms are ordered so that lowest
    # offset COME_FROM is last, it is sufficient to test
    # just the last one.
    # Note: We may find Example A defeats this rule.
    if len(tree) == 5:
        end_come_froms = tree[-1]
        if end_come_froms == "opt_come_from_except" and len(end_come_froms) > 0:
            end_come_froms = end_come_froms[0]
            pass
        while not isinstance(end_come_froms, Token) and len(end_come_froms):
            end_come_froms = end_come_froms[-1]
        if isinstance(end_come_froms, Token):
            if first_offset > end_come_froms.attr:
                return True
            elif first_offset > end_come_froms.attr:
                return True

    testexpr = tree[0]

    if_condition = testexpr[0]

    # Check that the condition portion of the "if"
    # jumps to the "else" part, and that the
    # end of the "then" portion jumps to a reasonable
    # place, e.g. not somewhere in the middle of the "else"
    # portion.
    if if_condition in ("testtrue", "testfalse", "and_cond"):

        then_end = tree[2]
        else_suite = tree[3]
        if else_suite == "else_suite_opt" and len(else_suite):
            else_suite = else_suite[0]

        if else_suite not in ("else_suite", "else_suitec"):
            # May need to handle later.
            return False

        # We may need this later:

        # not_or = if_condition[0]
        # if not_or == "not_or":
        #     # "if not_or" needs special attention to distinguish it from "if and".
        #     # If the jump is to the beginning of the "else" part, this is an "and".
        #     not_or_jump_expr = not_or[-1]
        #     if not_or_jump_expr == "_come_froms":
        #         not_or_jump_expr = not_or[-2]
        #     not_or_jump_offset = not_or_jump_expr.last_child().attr
        #     if not_or_jump_offset == else_suite.first_child().offset:
        #         return True

        # If there is a COME_FROM at the end, it (the outermost COME_FROM) needs to come
        # from within the "if-then" part
        if isinstance(then_end, Token):
            then_end_come_from = then_end
        else:
            then_end_come_from = then_end.last_child()

        if then_end_come_from == "COME_FROM" and then_end_come_from.attr < first_offset:
            return True

        # If there any instructions in the "then" part that jump to the beginning of the
        # "else" then this is not a proper if/else. Note that we might generalize this
        # to jump *anywhere* in the else body instead of the first instruction.
        else_start_offset = else_suite.first_child().off2int(prefer_last=False)

        then_start = tree[1].first_child()
        if then_start is None:
            return False

        then_start_offset = tree[1].first_child().off2int(prefer_last=False)

        i = self.offset2inst_index[then_start_offset]
        inst = self.insts[i]
        while inst.offset < else_start_offset:
            if inst.is_jump() and inst.argval == else_start_offset:
                return True
            i += 1
            inst = self.insts[i]

        if last_offset == -1:
            last_offset = tokens[last - 1].off2int(prefer_last=False)

        if else_suite == "else_suitec" and then_end in (
            "jb_elsec",
            "jb_cfs",
            "jump_forward_else",
        ):
            stmts = tree[1]
            jb_else = then_end
            come_from = jb_else[-1]
            if come_from in ("come_froms", "_come_froms") and len(come_from):
                come_from = come_from[-1]
            if come_from == "COME_FROM":
                if come_from.attr > stmts.first_child().off2int():
                    return True
                pass
            pass
        elif else_suite == "else_suite" and then_end == "jf_cfs":
            stmts = tree[1]
            jf_cfs = then_end
            if jf_cfs[0].attr < last_offset:
                return True

        if if_condition == "and_cond" and if_condition[1] == "expr_pjif":
            if_condition = if_condition[1]

        if_condition_last = if_condition.last_child()
        if if_condition_last.kind.startswith("POP_JUMP_IF_"):
            if last == n:
                last -= 1

            jmp = if_condition_last
            jump_target = jmp.attr

            # Below we check that jump_target is jumping to a feasible
            # location. It should be to the transition after the "then"
            # block and to the beginning of the "else" block.
            # However the "if/else" is inside a loop the false test can be
            # back to the loop.

            # FIXME: the below logic for jf_cfs could probably be
            # simplified.
            jump_else_end = tree[2]
            if jump_else_end == "jf_cf_pop":
                jump_else_end = jump_else_end[0]

            # jump_to_jump = False
            if jump_else_end == "JUMP_FORWARD":
                # jump_to_jump = True
                endif_target = int(jump_else_end.attr)
                if endif_target != last_offset:
                    return True

            if jump_target == last_offset:
                # jump_target should be jumping to the end of the if/then/else
                # but is it jumping to the beginning of the "else"
                return True
            if (
                jump_else_end in ("jf_cfs", "jump_forward_else")
                and jump_else_end[0] == "JUMP_FORWARD"
            ):
                # If the "else" jump jumps before the end of the the "if .. else end",
                # then this is not this kind of "ifelsestmt".
                jump_else_forward = jump_else_end[0]
                jump_else_forward_target = jump_else_forward.attr
                if jump_else_forward_target < last_offset:
                    return True
                pass
            if (
                jump_else_end in ("jf_cfs", "come_froms")
                and jump_else_end[-1] == "COME_FROM"
            ):
                if jump_else_end[-1].off2int() != jump_target:
                    return True

                # If the end of the "then" jumps to back to a loop,
                # then the end of the "else" must jump somewhere too
                # and not fall through.
                if jump_else_end == "jb_cfs":
                    i = self.offset2inst_index[last_offset]
                    inst = self.insts[i]
                    if not inst.is_jump():
                        return True
                    pass
                pass

            # If we have a jump_back, i.e we are in a loop, then a "end_then" of
            # the "else" can't be a fallthrough kind of instruction. In other
            # words, tokens[last] should have be a COME_FROM. Otherwise the
            # "else" suite should be extended to cover the next instruction at
            # tokens[last].
            if jump_else_end in ("jb_elsec", "jb_cfs") and tokens[last] not in (
                "COME_FROM",
                "JUMP_LOOP",
                "COME_FROM_LOOP",
            ):
                return True

            # If the part before the "else" statement doesn't have a JUMP in it,
            # i.e. is a "COME_FROM", then the statement before he COME_FROM should
            # not fallthrough. Otherwise we have an "if" statement, not "if/else".

            # if lhs == "ifelsestmtc":
            #     print("XXX", first, last, tokens[first], tokens[last])
            #     from trepan.api import debug; debug()

            if jump_else_end == "come_froms":
                jump_else_end = jump_else_end.last_child()
            if jump_else_end == "COME_FROM":
                come_from_offset = jump_else_end.off2int(prefer_last=False)
                before_come_from = self.insts[
                    self.offset2inst_index[come_from_offset] - 1
                ]
                # FIXME: When xdis next changes, this will be a field in the instruction
                no_follow = before_come_from.opcode in self.opc.nofollow
                return not (before_come_from.is_jump() or no_follow)

            if first_offset > jump_target:
                return True

            return (jump_target > last_offset) and tokens[last] != "JUMP_FORWARD"

    return False
