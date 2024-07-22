#  Copyright (c) 2020, 2022, 2024 Rocky Bernstein
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

NOT_POP_FOLLOW_OPS = frozenset(
    """
LOAD_ASSERT RAISE_VARARGS_1 STORE_FAST STORE_DEREF STORE_GLOBAL STORE_ATTR STORE_NAME
""".split()
)


def and_invalid(
    self, lhs: str, n: int, rule, tree, tokens: list, first: int, last: int
) -> bool:

    # print("XXX", first, last, rule)
    # for t in range(first, last): print(tokens[t])
    # print("="*40)

    # a LOAD_ASSERT is not an expression and not part of an "and"
    # FIXME: the below really should have been done in the ingest
    # phase.
    ltm1 = tokens[last - 1]
    rhs = rule[1]
    if ltm1 == "LOAD_ASSERT" or (
        ltm1 == "LOAD_GLOBAL" and ltm1.attr == "AssertionError"
    ):
        return True

    expr_pjif = tree[0]
    if expr_pjif == "expr_pjif":
        jump = expr_pjif[1]
    elif expr_pjif == "expr_jifop_cfs":
        expr_jifop_cfs = expr_pjif
        jump = expr_jifop_cfs[1]
        if expr_jifop_cfs[0][0] == "or":
            # FIXME check if the "or" jumps to the same place as jump.attr
            return True
        if first > 0:
            ftm1 = tokens[first - 1]
            if ftm1 == "JUMP_IF_TRUE_OR_POP" and ftm1.attr == jump.attr:
                return True
        else:
            jump = tree[1]

    elif rhs == ("and_parts", "expr") and expr_pjif[0] == "expr_pjif":
        expr_pjif = expr_pjif[0]
        jump = expr_pjif[1]
    else:
        # Probably not needed: was expr POP_JUMP_IF_FALSE
        jump = tree[1]

    if jump.kind.startswith("POP_JUMP_IF_"):
        if last == n:
            return True
        jump_target = jump.attr
        jump_offset = jump.offset

        if tokens[first].off2int() <= jump_target < tokens[last].off2int():
            return True

        if rule == ("and", ("expr_pjif", "expr_pjif")):
            jump2_target = tree[1][1].attr
            return jump_target != jump2_target
        elif rule == ("and", ("expr_pjif", "expr", "POP_JUMP_IF_TRUE")):
            jump2_target = tree[2].attr
            return jump_target == jump2_target
        elif rule == ("and", ("expr_pjif", "expr")):
            if tokens[last] == "POP_JUMP_IF_FALSE":
                # Ok if jump_target doesn't jump to last instruction
                return jump_target != tokens[last].attr
            elif tokens[last] in ("POP_JUMP_IF_TRUE", "JUMP_IF_TRUE_OR_POP"):
                # Ok if jump_target jumps to a COME_FROM after
                # the last instruction or jumps right after the last instruction
                if last + 1 < n and tokens[last + 1] == "COME_FROM":
                    return jump_target != tokens[last + 1].off2int()
                return jump_target + 2 != tokens[last].attr
        elif rule == ("and", ("expr_pjif", "expr", "COME_FROM")):
            return tree[-1].attr != jump_offset
        elif (
            rule == ("and", ("and_parts", "expr"))
            and jump_target > tokens[last].off2int()
            and tokens[last].kind.startswith("JUMP_IF_")
            and jump_target < tokens[last].attr
        ):
            # This could be an "(i and j) or k"
            # or:
            #    - and: expr, POP_JUMP_IF_FALSE jump_target, expr
            #    - JUMP_IF_TRUE_OR_POP end_or
            #    - jump_target: expr
            # end_or:
            return False

        return jump_target != tokens[last].off2int()
    return False
