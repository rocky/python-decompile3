#  Copyright (c) 2020-2022, 2024 Rocky Bernstein
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

from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG

from decompyle3.parsers.parse_heads import PythonBaseParser
from decompyle3.parsers.reduce_check import (
    break_invalid,
    for38_invalid,
    forelse38_invalid,
    pop_return_check,
    whilestmt38_check,
    whileTruestmt38_check,
)


class Python38PyPyBaseParser(PythonBaseParser):
    def __init__(self, start_symbol, debug_parser: dict = PARSER_DEFAULT_DEBUG):
        super(Python38PyPyBaseParser, self).__init__(
            start_symbol=start_symbol, debug_parser=debug_parser
        )

    def customize_grammar_rules38(self, tokens, customize):
        self.customize_grammar_rules37(tokens, customize)
        self.check_reduce["break"] = "tokens"
        self.check_reduce["for38"] = "tokens"
        self.check_reduce["forelsestmt38"] = "AST"
        self.check_reduce["pop_return"] = "tokens"
        self.check_reduce["whileTruestmt38"] = "AST"
        self.check_reduce["whilestmt38"] = "tokens"
        self.check_reduce["try_elsestmtl38"] = "AST"

        self.reduce_check_table["break"] = break_invalid
        self.reduce_check_table["for38"] = for38_invalid
        self.reduce_check_table["forelsestmt38"] = forelse38_invalid
        self.reduce_check_table["pop_return"] = pop_return_check
        self.reduce_check_table["whilestmt38"] = whilestmt38_check
        self.reduce_check_table["whileTruestmt38"] = whileTruestmt38_check
