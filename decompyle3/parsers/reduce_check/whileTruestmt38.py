#  Copyright (c) 2022-2023 Rocky Bernstein
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


def whileTruestmt38_check(
    self, lhs: str, n: int, rule, tree, tokens: list, first: int, last: int
) -> bool:
    # When we are missing a COME_FROM_LOOP, the
    # "while" statement is nested inside an if/else
    # so after the POP_BLOCK we have a JUMP_FORWARD which forms the "else" portion of the "if"
    # Check this.
    # print("XXX", first, last, rule)
    # for t in range(first, last): print(tokens[t])
    # print("="*40)

    if not tokens[last].kind.startswith("COME_FROM") and tokens[
        last - 1
    ].kind.startswith("COME_FROM"):
        last -= 1
    while tokens[last].kind.startswith("COME_FROM"):
        last -= 1
    if rule[-1][-1] == "\\e__come_froms":
        jump_loop = tree[-2]
    else:
        # This might not be needed
        jump_loop = tokens[last]
    if jump_loop == "JUMP_LOOP":
        jump_target = jump_loop.attr
        if jump_target < tokens[first].off2int(prefer_last=False):
            return True

        c_stmts = tree[1]
        if c_stmts == "c_stmts":
            # Distinguish:
            #   while True:
            #      if expr:
            # from:
            #   while expr:
            #
            # We distinguish by checking to see if the "if expr" jumps *outside* of
            # the loop bound.

            # First, see if we have "ifstmt" as the first statement inside "while True"
            c_stmts_offset = c_stmts.first_child().off2int()
            first_stmt = c_stmts[0]
            while first_stmt in ("_stmts", "stmts"):
                first_stmt = first_stmt[0]
            if first_stmt == "ifstmt":
                # Next check for a testexpr and get the last instruction of that
                testexpr = first_stmt[0]
                if testexpr == "testexpr":
                    pop_jump_if = testexpr.last_child()
                    # Do we have POP_JUMP_IF with a jump outside of the loop?
                    if (
                        pop_jump_if.kind.startswith("POP_JUMP_IF")
                        and pop_jump_if.attr > tokens[last].off2int()
                    ):
                        # Fail here, but we expect a "while expr" pattern to succeed elsewhere.
                        return True
            return c_stmts_offset != jump_target

    return False
