#  Copyright (c) 2017-2019 Rocky Bernstein
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
spark grammar differences over Python 3.6 for Python 3.7
"""
from __future__ import print_function

from decompyle3.parser import PythonParserSingle
from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from decompyle3.parsers.parse36 import Python36Parser

class Python37Parser(Python36Parser):

    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python37Parser, self).__init__(debug_parser)
        self.customized = {}

    def p_32on(self, args):
        """
        # Before Python 3.2, DUP_TOP_TWO is DUP_TOPX
        subscript2 ::= expr expr DUP_TOP_TWO BINARY_SUBSCR
        """
        return

    def p_33on(self, args):
        """
        # Python 3.3+ adds yield from.
        expr          ::= yield_from
        yield_from    ::= expr expr YIELD_FROM

        # We do the grammar hackery below for semantics
        # actions that want c_stmts_opt at index 1

        # Python 3.5+ has jump optimization to remove the redundant
        # jump_excepts. But in 3.3 we need them added

        try_except  ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                        except_handler
                        jump_excepts come_from_except_clauses
        """

    def p_32to35(self, args):
        """
        expr        ::= conditional
        conditional ::= expr jmp_false expr jump_forward_else expr COME_FROM

        # compare_chained2 is used in a "chained_compare": x <= y <= z
        # used exclusively in compare_chained
        compare_chained2 ::= expr COMPARE_OP RETURN_VALUE
        compare_chained2 ::= expr COMPARE_OP RETURN_VALUE_LAMBDA

        # Python < 3.5 no POP BLOCK
        whileTruestmt  ::= SETUP_LOOP l_stmts_opt JUMP_BACK COME_FROM_LOOP

        # Python 3.5+ has jump optimization to remove the redundant
        # jump_excepts. But in 3.3 we need them added

        try_except     ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                           except_handler
                           jump_excepts come_from_except_clauses

        except_handler ::= JUMP_FORWARD COME_FROM_EXCEPT except_stmts
                           END_FINALLY

        tryelsestmt    ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                           except_handler else_suite
                           jump_excepts come_from_except_clauses

        jump_excepts   ::= jump_except+

        # Python 3.2+ has more loop optimization that removes
        # JUMP_FORWARD in some cases, and hence we also don't
        # see COME_FROM
        _ifstmts_jump ::= c_stmts_opt
        _ifstmts_jump ::= c_stmts_opt JUMP_FORWARD _come_froms

        kv3       ::= expr expr STORE_MAP
        """
        return

    def p_34on(self, args):
        """
        expr ::= LOAD_ASSERT

        # passtmt is needed for semantic actions to add "pass"
        suite_stmts_opt ::= pass

        whilestmt     ::= SETUP_LOOP testexpr returns come_froms POP_BLOCK COME_FROM_LOOP

        # Seems to be needed starting 3.4.4 or so
        while1stmt    ::= SETUP_LOOP l_stmts
                          COME_FROM JUMP_BACK POP_BLOCK COME_FROM_LOOP
        while1stmt    ::= SETUP_LOOP l_stmts
                          POP_BLOCK COME_FROM_LOOP

        # FIXME the below masks a bug in not detecting COME_FROM_LOOP
        # grammar rules with COME_FROM -> COME_FROM_LOOP already exist
        whileelsestmt     ::= SETUP_LOOP testexpr l_stmts_opt JUMP_BACK POP_BLOCK
                              else_suitel COME_FROM

        while1elsestmt    ::= SETUP_LOOP l_stmts JUMP_BACK _come_froms POP_BLOCK else_suitel
                              COME_FROM_LOOP

        # Python 3.4+ optimizes the trailing two JUMPS away

        _ifstmts_jump ::= c_stmts_opt JUMP_ABSOLUTE JUMP_FORWARD COME_FROM
        """

    def p_37misc(self, args):
        """
        # Where does the POP_TOP really belong?
        stmt     ::= import37
        stmt     ::= async_for_stmt37
        import37 ::= import POP_TOP

        async_for_stmt     ::= SETUP_LOOP expr
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

        # Order of LOAD_CONST YIELD_FROM is switched from 3.6 to save a LOAD_CONST
        async_for_stmt37   ::= SETUP_LOOP expr
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

        async_forelse_stmt ::= SETUP_LOOP expr
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

        attributes ::= IMPORT_FROM ROT_TWO POP_TOP IMPORT_FROM
        attributes ::= attributes ROT_TWO POP_TOP IMPORT_FROM

        attribute37   ::= expr LOAD_METHOD
        expr          ::= attribute37

        # FIXME: generalize and specialize
        call        ::= expr CALL_METHOD_0

        testtrue         ::= compare_chained37
        testfalse        ::= compare_chained37_false


        compare_chained37   ::= expr compare_chained1a_37
        compare_chained37   ::= expr compare_chained1b_37
        compare_chained37   ::= expr compare_chained1c_37

        compare_chained37_false  ::= expr compare_chained1_false_37
        compare_chained37_false  ::= expr compare_chained2_false_37

        compare_chained1a_37      ::= expr DUP_TOP ROT_THREE COMPARE_OP POP_JUMP_IF_FALSE
        compare_chained1a_37      ::= expr DUP_TOP ROT_THREE COMPARE_OP POP_JUMP_IF_FALSE
                                      compare_chained2a_37 ELSE POP_TOP COME_FROM
        compare_chained1b_37      ::= expr DUP_TOP ROT_THREE COMPARE_OP POP_JUMP_IF_FALSE
                                      compare_chained2b_37 POP_TOP JUMP_FORWARD COME_FROM
        compare_chained1c_37      ::= expr DUP_TOP ROT_THREE COMPARE_OP POP_JUMP_IF_FALSE
                                      compare_chained2a_37 POP_TOP

        compare_chained1_false_37 ::= expr DUP_TOP ROT_THREE COMPARE_OP POP_JUMP_IF_FALSE
                                      compare_chained2c_37 POP_TOP JUMP_FORWARD COME_FROM
        compare_chained2_false_37 ::= expr DUP_TOP ROT_THREE COMPARE_OP POP_JUMP_IF_FALSE
                                      compare_chained2a_false_37 ELSE POP_TOP JUMP_BACK COME_FROM

        compare_chained2a_37       ::= expr COMPARE_OP POP_JUMP_IF_TRUE JUMP_FORWARD
        compare_chained2a_37       ::= expr COMPARE_OP POP_JUMP_IF_TRUE JUMP_BACK
        compare_chained2a_false_37 ::= expr COMPARE_OP POP_JUMP_IF_FALSE jf_cfs

        compare_chained2b_37       ::= expr COMPARE_OP come_from_opt POP_JUMP_IF_FALSE JUMP_FORWARD ELSE
        compare_chained2b_37       ::= expr COMPARE_OP come_from_opt POP_JUMP_IF_FALSE JUMP_FORWARD

        compare_chained2c_37       ::= expr DUP_TOP ROT_THREE COMPARE_OP come_from_opt POP_JUMP_IF_FALSE
                                       compare_chained2a_false_37 ELSE
        compare_chained2c_37       ::= expr DUP_TOP ROT_THREE COMPARE_OP come_from_opt POP_JUMP_IF_FALSE
                                       compare_chained2a_false_37

        jf_cfs                     ::= JUMP_FORWARD _come_froms
        ifelsestmt                 ::= testexpr c_stmts_opt jf_cfs else_suite opt_come_from_except

        jmp_false37                ::= POP_JUMP_IF_FALSE COME_FROM
        list_if                    ::= expr jmp_false37 list_iter

        _ifstmts_jump              ::= c_stmts_opt come_froms

        and_not                    ::= expr jmp_false expr POP_JUMP_IF_TRUE

        expr                       ::= if_exp_37a
        expr                       ::= if_exp_37b
        if_exp_37a                 ::= and_not expr JUMP_FORWARD COME_FROM expr COME_FROM
        if_exp_37b                 ::= expr jmp_false expr POP_JUMP_IF_FALSE jump_forward_else expr
        """

    def customize_grammar_rules(self, tokens, customize):
        self.remove_rules("""
          async_forelse_stmt ::= SETUP_LOOP expr
                                 GET_AITER
                                 LOAD_CONST YIELD_FROM SETUP_EXCEPT GET_ANEXT LOAD_CONST
                                 YIELD_FROM
                                 store
                                 POP_BLOCK JUMP_FORWARD COME_FROM_EXCEPT DUP_TOP
                                 LOAD_GLOBAL COMPARE_OP POP_JUMP_IF_FALSE
                                 POP_TOP POP_TOP POP_TOP POP_EXCEPT POP_BLOCK
                                 JUMP_ABSOLUTE END_FINALLY COME_FROM
                                 for_block POP_BLOCK
                                 else_suite COME_FROM_LOOP
        stmt      ::= async_for_stmt36
        async_for_stmt36   ::= SETUP_LOOP expr
                               GET_AITER
                               LOAD_CONST YIELD_FROM SETUP_EXCEPT GET_ANEXT LOAD_CONST
                               YIELD_FROM
                               store
                               POP_BLOCK JUMP_BACK COME_FROM_EXCEPT DUP_TOP
                               LOAD_GLOBAL COMPARE_OP POP_JUMP_IF_TRUE
                               END_FINALLY continues COME_FROM
                               POP_TOP POP_TOP POP_TOP POP_EXCEPT
                               POP_TOP POP_BLOCK
                               COME_FROM_LOOP
        """)
        super(Python37Parser, self).customize_grammar_rules(tokens, customize)

class Python37ParserSingle(Python37Parser, PythonParserSingle):
    pass

if __name__ == '__main__':
    # Check grammar
    p = Python37Parser()
    p.check_grammar()
    from decompyle3 import PYTHON_VERSION, IS_PYPY
    if PYTHON_VERSION == 3.7:
        lhs, rhs, tokens, right_recursive = p.check_sets()
        from decompyle3.scanner import get_scanner
        s = get_scanner(PYTHON_VERSION, IS_PYPY)
        opcode_set = set(s.opc.opname).union(set(
            """JUMP_BACK CONTINUE RETURN_END_IF COME_FROM
               LOAD_GENEXPR LOAD_ASSERT LOAD_SETCOMP LOAD_DICTCOMP LOAD_CLASSNAME
               LAMBDA_MARKER RETURN_LAST
            """.split()))
        remain_tokens = set(tokens) - opcode_set
        import re
        remain_tokens = set([re.sub(r'_\d+$', '', t) for t in remain_tokens])
        remain_tokens = set([re.sub('_CONT$', '', t) for t in remain_tokens])
        remain_tokens = set(remain_tokens) - opcode_set
        print(remain_tokens)
        # print(sorted(p.rule2name.items()))
