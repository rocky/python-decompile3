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

from decompyle3.parsers.treenode import SyntaxTree

def c_tryelsestmt(self, lhs, n, rule, ast, tokens, first, last):
    # Check the end of the except handler that there isn't a jump from
    # inside the except handler to the end. If that happens
    # then this is a "try" with no "else".
    except_handler = ast[3]

    if except_handler == "except_handler_else":
        except_handler = except_handler[0]

    come_from = except_handler[-1]
    # We only care about the *first* come_from because that is the
    # the innermost one. So if the "tryelse" is invalid (should be a "try")
    # it will be invalid here.
    if come_from == "COME_FROM":
        first_come_from = except_handler[-1]
    elif come_from == "END_FINALLY":
        return False
    elif come_from == "except_return":
        return False
    else:
        assert come_from in ("come_froms", "opt_come_from_except")
        first_come_from = come_from[0]
        if not hasattr(first_come_from, "attr"):
            # optional come from
            return False

    leading_jump = except_handler[0]
    if not hasattr(leading_jump, "offset"):
        return False

    # We really don't care that this is a jump per-se. But
    # we could also check that this jumps to the end of the except if
    # desired.
    if isinstance(leading_jump, SyntaxTree):
        except_handler_first_offset = leading_jump.first_child().off2int()
    else:
        except_handler_first_offset = leading_jump.off2int()

    return first_come_from.attr > except_handler_first_offset
