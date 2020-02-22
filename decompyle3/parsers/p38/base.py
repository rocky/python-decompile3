#  Copyright (c) 2020 Rocky Bernstein
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

from decompyle3.parsers.main import PythonParserSingle
from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from decompyle3.parsers.p38.full import Python38FullParser
from decompyle3.parsers.reducecheck import (
    break_check,
    for38_check,
    pop_return_check
)

class Python38Parser(Python38FullParser):
    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG, compile_mode="exec"):
        super(Python38Parser, self).__init__(debug_parser, compile_mode=compile_mode)
        self.customized = {}

    def remove_rules_38(self):
        self.remove_rules(
            """
           stmt               ::= async_for_stmt37
           stmt               ::= for
           stmt               ::= forelsestmt
           stmt               ::= try_except36
           stmt               ::= async_forelse_stmt

           async_for_stmt     ::= setup_loop expr
                                  GET_AITER
                                  SETUP_EXCEPT GET_ANEXT LOAD_CONST
                                  YIELD_FROM
                                  store
                                  POP_BLOCK JUMP_FORWARD COME_FROM_EXCEPT DUP_TOP
                                  LOAD_GLOBAL COMPARE_OP POP_JUMP_IF_TRUE
                                  END_FINALLY COME_FROM
                                  for_block
                                  COME_FROM
                                  POP_TOP POP_TOP POP_TOP POP_EXCEPT POP_TOP POP_BLOCK
                                  COME_FROM_LOOP
           async_for_stmt37   ::= setup_loop expr
                                  GET_AITER
                                  SETUP_EXCEPT GET_ANEXT
                                  LOAD_CONST YIELD_FROM
                                  store
                                  POP_BLOCK JUMP_BACK COME_FROM_EXCEPT DUP_TOP
                                  LOAD_GLOBAL COMPARE_OP POP_JUMP_IF_TRUE
                                  END_FINALLY for_block COME_FROM
                                  POP_TOP POP_TOP POP_TOP POP_EXCEPT
                                  POP_TOP POP_BLOCK
                                  COME_FROM_LOOP

          async_forelse_stmt ::= setup_loop expr
                                 GET_AITER
                                 SETUP_EXCEPT GET_ANEXT LOAD_CONST
                                 YIELD_FROM
                                 store
                                 POP_BLOCK JUMP_FORWARD COME_FROM_EXCEPT DUP_TOP
                                 LOAD_GLOBAL COMPARE_OP POP_JUMP_IF_TRUE
                                 END_FINALLY COME_FROM
                                 for_block
                                 COME_FROM
                                 POP_TOP POP_TOP POP_TOP POP_EXCEPT POP_TOP POP_BLOCK
                                 else_suite COME_FROM_LOOP

           for                ::= setup_loop expr get_for_iter store for_block POP_BLOCK
           for                ::= setup_loop expr get_for_iter store for_block POP_BLOCK NOP

           for_block          ::= c_stmts_opt COME_FROM_LOOP JUMP_BACK
           forelsestmt        ::= setup_loop expr get_for_iter store for_block POP_BLOCK else_suite
           forelselaststmt    ::= setup_loop expr get_for_iter store for_block POP_BLOCK else_suitec
           forelselaststmtc   ::= setup_loop expr get_for_iter store for_block POP_BLOCK else_suitec

           try_except         ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                                  except_handler opt_come_from_except

           tryfinallystmt     ::= SETUP_FINALLY suite_stmts_opt POP_BLOCK
                                  LOAD_CONST COME_FROM_FINALLY suite_stmts_opt
                                  END_FINALLY
           tryfinally36       ::= SETUP_FINALLY returns
                                  COME_FROM_FINALLY suite_stmts_opt END_FINALLY
           tryfinally_return_stmt ::= SETUP_FINALLY suite_stmts_opt POP_BLOCK
                                      LOAD_CONST COME_FROM_FINALLY
        """
        )

    def customize_grammar_rules(self, tokens, customize):
        super(Python38Parser, self).customize_grammar_rules(tokens, customize)
        self.remove_rules_38()
        self.check_reduce["break"] = "tokens"
        self.check_reduce["for38"] = "tokens"
        self.check_reduce["pop_return"] = "tokens"
        self.check_reduce["whileTruestmt38"] = "tokens"
        self.check_reduce["whilestmt38"] = "tokens"
        self.check_reduce["try_elsestmtl38"] = "AST"

        self.reduce_check_table["break"] = break_check
        self.reduce_check_table["for38"] = for38_check
        self.reduce_check_table["pop_return"] = pop_return_check

    def reduce_is_invalid(self, rule, ast, tokens, first, last):
        invalid = super(Python38Parser, self).reduce_is_invalid(
            rule, ast, tokens, first, last
        )
        if invalid:
            return invalid
        lhs = rule[0]
        if lhs in ("whileTruestmt38", "whilestmt38"):
            jb_index = last - 1
            while jb_index > 0 and tokens[jb_index].kind.startswith("COME_FROM"):
                jb_index -= 1
            t = tokens[jb_index]
            if t.kind != "JUMP_BACK":
                return True
            return t.attr != tokens[first].off2int()
            pass

        return False

class Python38ParserSingle(Python38Parser, PythonParserSingle):
    pass


if __name__ == "__main__":
    # Check grammar
    from decompyle3.parsers.dump import dump_and_check
    p = Python38Parser()
    modified_tokens = set(
        """JUMP_BACK CONTINUE RETURN_END_IF COME_FROM
           LOAD_GENEXPR LOAD_ASSERT LOAD_SETCOMP LOAD_DICTCOMP LOAD_CLASSNAME
           LAMBDA_MARKER RETURN_LAST
        """.split()
        )

    p.remove_rules_38()
    dump_and_check(p, 3.8, modified_tokens)
