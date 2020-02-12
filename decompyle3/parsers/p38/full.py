#  Copyright (c) 2017-2020 Rocky Bernstein
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
spark grammar differences over Python 3.7 for Python 3.8
"""

from decompyle3.parsers.main import PythonParserSingle
from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from decompyle3.parsers.p37.full import Python37Parser

class Python38Parser(Python37Parser):
    def p_38walrus(self, args):
        """
        # named_expr is also known as the "walrus op" :=
        expr              ::= named_expr
        named_expr        ::= expr DUP_TOP store
        """

    def p_38misc(self, args):
        """
        stmt               ::= async_for_stmt38
        stmt               ::= async_forelse_stmt38
        stmt               ::= for38
        stmt               ::= forelsestmt38
        stmt               ::= forelselaststmt38
        stmt               ::= forelselaststmtc38
        stmt               ::= tryfinally38stmt
        stmt               ::= tryfinally38rstmt
        stmt               ::= tryfinally38astmt
        stmt               ::= try_elsestmtl38
        stmt               ::= try_except_ret38
        stmt               ::= try_except38
        stmt               ::= whilestmt38
        stmt               ::= whileTruestmt38
        stmt               ::= call

        break ::= POP_BLOCK BREAK_LOOP
        break ::= POP_BLOCK POP_TOP BREAK_LOOP
        break ::= POP_TOP BREAK_LOOP
        break ::= POP_EXCEPT BREAK_LOOP

        # FIXME: this should be restricted to being inside a try block
        stmt               ::= except_ret38

        # FIXME: this should be added only when seeing GET_AITER or YIELD_FROM
        async_for_stmt38   ::= expr
                               GET_AITER
                               SETUP_FINALLY
                               GET_ANEXT
                               LOAD_CONST
                               YIELD_FROM
                               POP_BLOCK
                               store for_block
                               COME_FROM_FINALLY
                               END_ASYNC_FOR

        # FIXME: come froms after the else_suite or END_ASYNC_FOR distinguish which of
        # for / forelse is used. Add come froms and check of add up control-flow detection phase.
        async_forelse_stmt38 ::= expr
                               GET_AITER
                               SETUP_FINALLY
                               GET_ANEXT
                               LOAD_CONST
                               YIELD_FROM
                               POP_BLOCK
                               store for_block
                               COME_FROM_FINALLY
                               END_ASYNC_FOR
                               else_suite

        return             ::= ret_expr ROT_TWO POP_TOP RETURN_VALUE

        # 3.8 can push a looping JUMP_BACK into into a JUMP_ from a statement that jumps to it
        lastc_stmt         ::= ifpoplaststmtc
        ifpoplaststmtc     ::= testexpr POP_TOP c_stmts_opt
        ifelsestmtc        ::= testexpr c_stmts_opt jb_cfs else_suitec JUMP_BACK come_froms

        # Keep indices the same in ifelsestmtc
        cf_pt              ::= COME_FROM POP_TOP
        ifelsestmtc        ::= testexpr c_stmts cf_pt else_suite

        get_iter           ::= expr GET_ITER
        for38              ::= expr get_iter store for_block JUMP_BACK
        for38              ::= expr get_for_iter store for_block JUMP_BACK
        for38              ::= expr get_for_iter store for_block JUMP_BACK POP_BLOCK
        for38              ::= expr get_for_iter store for_block

        forelsestmt38      ::= expr get_for_iter store for_block POP_BLOCK else_suite
        forelselaststmt38  ::= expr get_for_iter store for_block POP_BLOCK else_suitec
        forelselaststmtc38 ::= expr get_for_iter store for_block POP_BLOCK else_suitec

        whilestmt38        ::= _come_froms testexpr c_stmts_opt COME_FROM JUMP_BACK POP_BLOCK
        whilestmt38        ::= _come_froms testexpr c_stmts_opt JUMP_BACK POP_BLOCK
        whilestmt38        ::= _come_froms testexpr c_stmts_opt JUMP_BACK come_froms
        whilestmt38        ::= _come_froms testexpr returns               POP_BLOCK
        whilestmt38        ::= _come_froms testexpr c_stmts     JUMP_BACK
        whilestmt38        ::= _come_froms testexpr c_stmts     come_froms

        # while1elsestmt   ::=          c_stmts     JUMP_BACK
        whileTruestmt      ::= _come_froms c_stmts              JUMP_BACK POP_BLOCK
        while1stmt         ::= _come_froms c_stmts COME_FROM_LOOP
        while1stmt         ::= _come_froms c_stmts COME_FROM JUMP_BACK COME_FROM_LOOP
        whileTruestmt38    ::= _come_froms c_stmts JUMP_BACK
        whileTruestmt38    ::= _come_froms c_stmts JUMP_BACK COME_FROM_EXCEPT_CLAUSE

        for_block          ::= _come_froms c_stmts_opt come_from_loops JUMP_BACK

        except_cond1       ::= DUP_TOP expr COMPARE_OP jmp_false
                               POP_TOP POP_TOP POP_TOP
                               POP_EXCEPT

        try_elsestmtl38    ::= SETUP_FINALLY suite_stmts_opt POP_BLOCK
                               except_handler38 COME_FROM
                               else_suitec opt_come_from_except
        try_except         ::= SETUP_FINALLY suite_stmts_opt POP_BLOCK
                               except_handler38
        try_except38       ::= SETUP_FINALLY POP_BLOCK POP_TOP suite_stmts_opt
                               except_handler38a
        try_except_ret38   ::= SETUP_FINALLY expr POP_BLOCK
                               RETURN_VALUE except_ret38a

        # Note: there is a suite_stmts_opt which seems
        # to be bookkeeping which is not expressed in source code
        except_ret38       ::= SETUP_FINALLY expr ROT_FOUR POP_BLOCK POP_EXCEPT
                               CALL_FINALLY RETURN_VALUE COME_FROM
                               COME_FROM_FINALLY
                               suite_stmts_opt END_FINALLY
        except_ret38a      ::= COME_FROM_FINALLY POP_TOP POP_TOP POP_TOP
                               expr ROT_FOUR
                               POP_EXCEPT RETURN_VALUE END_FINALLY

        except_handler38   ::= jump COME_FROM_FINALLY
                               except_stmts END_FINALLY opt_come_from_except
        except_handler38a  ::= COME_FROM_FINALLY POP_TOP POP_TOP POP_TOP
                               POP_EXCEPT POP_TOP stmts END_FINALLY

        tryfinallystmt     ::= SETUP_FINALLY suite_stmts_opt POP_BLOCK
                               BEGIN_FINALLY COME_FROM_FINALLY suite_stmts_opt
                               END_FINALLY


        lc_setup_finally   ::= LOAD_CONST SETUP_FINALLY
        call_finally_pt    ::= CALL_FINALLY POP_TOP
        cf_cf_finally      ::= come_from_opt COME_FROM_FINALLY
        pop_finally_pt     ::= POP_FINALLY POP_TOP


        tryfinally38rstmt  ::= lc_setup_finally POP_BLOCK call_finally_pt
                               returns
                               cf_cf_finally pop_finally_pt
                               suite_stmts
                               END_FINALLY POP_TOP
        tryfinally38rstmt  ::= SETUP_FINALLY POP_BLOCK CALL_FINALLY
                               returns
                               cf_cf_finally END_FINALLY
                               suite_stmts
        tryfinally38rstmt  ::= SETUP_FINALLY POP_BLOCK CALL_FINALLY
                               returns
                               cf_cf_finally POP_FINALLY
                               suite_stmts
                               END_FINALLY
        tryfinally38rstmt  ::= SETUP_FINALLY POP_BLOCK CALL_FINALLY
                               returns
                               COME_FROM_FINALLY POP_FINALLY
                               suite_stmts
                               END_FINALLY

        tryfinally38stmt   ::= SETUP_FINALLY suite_stmts_opt POP_BLOCK
                               BEGIN_FINALLY COME_FROM_FINALLY
                               POP_FINALLY suite_stmts_opt END_FINALLY

        tryfinally38astmt  ::= LOAD_CONST SETUP_FINALLY suite_stmts_opt POP_BLOCK
                               BEGIN_FINALLY COME_FROM_FINALLY
                               POP_FINALLY POP_TOP suite_stmts_opt END_FINALLY POP_TOP
        """

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

           tryelsestmtc3      ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                                  except_handler COME_FROM else_suitec
                                  opt_come_from_except
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
        super(Python37Parser, self).customize_grammar_rules(tokens, customize)
        self.remove_rules_38()
        self.check_reduce["whileTruestmt38"] = "tokens"
        self.check_reduce["whilestmt38"] = "tokens"
        self.check_reduce["try_elsestmtl38"] = "AST"

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
    dump_and_check(p, 3.7, modified_tokens)
