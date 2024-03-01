#  Copyright (c) 2020-2024 Rocky Bernstein
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
"""
Differences over Python 3.7 for Python 3.8 in the Earley-algorithm lambda grammar
"""

from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG

from decompyle3.parsers.p37.lambda_expr import Python37LambdaParser
from decompyle3.parsers.p38pypy.lambda_custom import Python38PyPyLambdaCustom
from decompyle3.parsers.parse_heads import PythonBaseParser, PythonParserLambda


class Python38PyPyLambdaParser(
    Python38PyPyLambdaCustom, Python37LambdaParser, PythonParserLambda
):
    def p_38walrus(self, args):
        """
        # named_expr is also known as the "walrus op" :=
        expr              ::= named_expr
        named_expr        ::= expr DUP_TOP store
        """

    def p_lambda_start(self, args):
        """
        return_expr_lambda ::= genexpr_func LOAD_CONST RETURN_VALUE_LAMBDA
        """

    def p_pypy38_comprehension(self, args):
        """
        list_comp  ::= LOAD_ARG
                       BUILD_LIST_FROM_ARG
                       COME_FROM FOR_ITER
                       store lc_body
                       JUMP_LOOP _come_froms

        list_afor2 ::= async_iter store list_iter
                       JUMP_LOOP COME_FROM_EXCEPT
                       END_ASYNC_FOR


        lc_body ::= expr LIST_APPEND
        """

    def p_expr38(self, args):
        """
        expr ::= if_exp_compare38

        if_exp_compare38 ::= or_in_ifexp jump_if_false_cf expr jf_cfs expr come_froms

        list_iter        ::= list_if_not38
        list_if_not38    ::= expr pjump_ift expr pjump_ift _come_froms list_iter
                             come_from_opt

        or_in_ifexp      ::= expr_pjit expr
        or_in_ifexp      ::= or_in_ifexp POP_JUMP_IF_TRUE expr
        """

    def __init__(
        self,
        start_symbol: str = "lambda_start",
        debug_parser: dict = PARSER_DEFAULT_DEBUG,
    ):
        PythonParserLambda.__init__(
            self, debug_parser=debug_parser, start_symbol=start_symbol
        )
        PythonBaseParser.__init__(
            self, start_symbol=start_symbol, debug_parser=debug_parser
        )
        Python38PyPyLambdaCustom.__init__(self)

    def customize_grammar_rules(self, tokens, customize):
        self.customize_grammar_rules_lambda38(tokens, customize)


if __name__ == "__main__":
    # Check grammar
    from decompyle3.parsers.dump import dump_and_check

    p = Python38PyPyLambdaParser()
    modified_tokens = set(
        """JUMP_LOOP CONTINUE RETURN_END_IF COME_FROM
           LOAD_GENEXPR LOAD_ASSERT LOAD_SETCOMP LOAD_DICTCOMP LOAD_CLASSNAME
           LAMBDA_MARKER RETURN_LAST
        """.split()
    )

    dump_and_check(p, (3, 8), modified_tokens)
