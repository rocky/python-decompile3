#  Copyright (c) 2020 Rocky Bernstein
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

def and_check(
    self, lhs: str, n: int, rule, ast, tokens: list, first: int, last: int
) -> bool:
    jump = ast[1]
    if jump.kind.startswith("jump_if_"):
        if last == n:
            return True
        jump_target = jump[0].attr
        jump_offset = jump[0].offset

        if tokens[first].off2int() <= jump_target < tokens[last].off2int():
            return True
        if rule == ("and", ("expr", "jump_if_false", "expr", "jump_if_false")):
            jump2_target = ast[3][0].attr
            return jump_target != jump2_target
        elif rule == ("and", ("expr", "jump_if_false", "expr", "POP_JUMP_IF_TRUE")):
            jump2_target = ast[3].attr
            return jump_target == jump2_target
        elif rule == ("and", ("expr", "jump_if_false", "expr")):
            if tokens[last] == "POP_JUMP_IF_FALSE":
                # Ok if jump_target doesn't jump to last instruction
                return jump_target != tokens[last].attr
            elif tokens[last] in ("POP_JUMP_IF_TRUE", "JUMP_IF_TRUE_OR_POP"):
                # Ok if jump_target jumps to a COME_FROM after
                # the last instruction or jumps right after last instruction
                if last + 1 < n and tokens[last + 1] == "COME_FROM":
                    return jump_target != tokens[last + 1].off2int()
                return jump_target + 2 != tokens[last].attr
        elif rule == ("and", ("expr", "jump_if_false", "expr", "COME_FROM")):
            return ast[-1].attr != jump_offset
        # elif rule == ("and", ("expr", "jump_if_false", "expr", "COME_FROM")):
        #     return jump_offset != tokens[first+3].attr

        return jump_target != tokens[last].off2int()
    return False
