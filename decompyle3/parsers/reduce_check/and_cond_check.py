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


def and_cond_check(
    self, lhs: str, n: int, rule, ast, tokens: list, first: int, last: int
) -> bool:
    rhs = rule[1]
    if rhs[0] in ("and_parts", "testfalse") and rhs[1] == "expr_pjif":
        and_parts = ast[0]
        last_expr_pjif = ast[1]
        test_jump_target = last_expr_pjif[-1].attr
        expr_pjif = and_parts[0]
        while expr_pjif == "and_parts":
            expr_pjif = expr_pjif[0]
            if expr_pjif == "expr_pjif" and test_jump_target != expr_pjif[-1].attr:
                return True
            pass
        if expr_pjif == "expr_pjif":
            return test_jump_target != expr_pjif[-1].attr
    return False
