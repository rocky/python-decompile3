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


# FIXME: we need to distinguish "or" as an expression which doesn't have
# a "POP" instruction and "or" as a condition which does have the "POP"
# instruction. Until then we use NOT_POP_FOLLOW_UPS as a hack to distinguish the
# two
NOT_POP_FOLLOW_OPS = frozenset(
    """
LOAD_ASSERT RAISE_VARARGS_1 STORE_FAST STORE_DEREF STORE_GLOBAL STORE_ATTR STORE_NAME
""".split()
)


def or_check37_invalid(
    self, lhs: str, n: int, rule, ast, tokens: list, first: int, last: int
) -> bool:

    expr_pjit = ast[0]
    if expr_pjit in ("expr_pjit", "or_parts"):

        if expr_pjit == "or_parts":
            expr_pjit = expr_pjit[0]
        if expr_pjit != "expr_pjit":
            return False

        # See FIXME: above
        if tokens[last] in NOT_POP_FOLLOW_OPS or tokens[last - 1] in NOT_POP_FOLLOW_OPS:
            return True

        # The following test needs to prevent "or" from being
        # mistaken for part of an "assert"t statement.

        # The below then is useful until we get better control-flow analysis.
        # Note it is too hard in the scanner right nowto turn the LOAD_GLOBAL into
        # into LOAD_ASSERT. However in 3.9ish code generation does this by default.
        load_global = tokens[last - 1]
        if load_global == "LOAD_GLOBAL" and load_global.attr == "AssertionError":
            return True

        first_offset = tokens[first].off2int()
        jump_if_true_target = expr_pjit[1].attr
        if jump_if_true_target < first_offset:
            return False

        jump_if_false = tokens[last]
        # If the jmp is backwards
        if jump_if_false.kind.startswith("POP_JUMP_IF_FALSE"):
            jump_if_false_offset = jump_if_false.off2int()
            if jump_if_false == "POP_JUMP_IF_FALSE_LOOP":
                # For a backwards loop, well compare to the instruction *after*
                # then POP_JUMP...
                jump_if_false = tokens[last + 1]
            return not (
                (
                    jump_if_false_offset
                    <= jump_if_true_target
                    <= jump_if_false_offset + 2
                )
                or jump_if_true_target < tokens[first].off2int()
            )

    return False
