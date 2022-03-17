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


def if_and_stmt(
    self, lhs: str, n: int, rule, ast, tokens: list, first: int, last: int
) -> bool:
    # Make sure jumps don't extend beyond the end of the if statement.
    last_offset = tokens[last].off2int()
    for i in range(first, last):
        t = tokens[i]
        # instead of POP_JUMP_IF, should we use op attributes?
        if t.kind.startswith("POP_JUMP_IF_"):
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

    if rule[1][:-1] == ("expr_pjif", "expr", "COME_FROM", "stmts"):
        # POP_JUMP_IF_FALSE should go to the COME_FROM
        return ast[2].attr != ast[0][1].off2int(prefer_last=False)
    else:
        end_if_jump = ast[1]
        end_if_offset = end_if_jump.attr
        # stmts = ast[-2]
        # come_froms = ast[-1]
        return end_if_offset < tokens[last].off2int(prefer_last=False)
