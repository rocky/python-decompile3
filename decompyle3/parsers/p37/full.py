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

from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from decompyle3.parsers.main import PythonParserSingle
from decompyle3.parsers.p37.lambda_expr import Python37LambdaParser

class Python37Parser(Python37LambdaParser):
    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG, compile_mode="exec"):
        super(Python37Parser, self).__init__(debug_parser, compile_mode=compile_mode)
        self.customized = {}

    ###############################################
    #  Python 3.7 grammar rules with statements
    ###############################################
    def p_start(self, args):
        """
        # The start or goal symbol
        stmts ::= sstmt+
        """

    def p_call_stmt(self, args):
        """
        # eval-mode compilation.  Single-mode interactive compilation
        # adds another rule.
        call_stmt ::= expr POP_TOP
        """

    def p_stmt_loop(self, args):
        """
        #########################################################
        # Higher-level rules for statements in some sort of loop.
        #
        # Loops allow "continue" and "break" at the Python level.
        # At the bytecode level, there are backward jumps.
        #
        # Productions that can appear outside of
        # loop should be derivable from inside a loop, but
        # not necessarily vice versa, such as for "BREAK"
        # and "CONTINUE" (pseudo or real) instructions.
        #
        # Nonterminal names that start "c_" or end in "c", indicates
        # rule that can only to appear in a loop.
        # (The "c" stands for "continue". It is
        # a little bit historical. "l" was considered but can
        # be confused with "last".)
        #
        # Lower-level rules are with looping are mixed with their
        # non-looping equivalent.
        #########################################################
        c_stmts ::= _stmts
        c_stmts ::= _stmts lastc_stmt
        c_stmts ::= lastc_stmt
        c_stmts ::= continues
        c_stmts ::= c_stmt+
        c_stmts ::= returns

        c_stmt  ::= stmt
        c_stmt  ::= ifelsestmtc
        c_stmt  ::= ifstmtc
        c_stmt  ::= break
        c_stmt  ::= continue
        c_stmt  ::= c_try_except

        c_stmts_opt ::= c_stmts
        c_stmts_opt ::= pass

        lastc_stmt ::= forelselaststmtc
        lastc_stmt ::= iflaststmtc

        # FIXME: Do we need these?
        lastc_stmt ::= ifelsestmtc
        lastc_stmt ::= tryelsestmtc

        else_suitec ::= c_stmts
        else_suitec ::= returns
        else_suitec ::= suite_stmts

        c_suite_stmts     ::= c_stmts
        c_suite_stmts     ::= suite_stmts
        c_suite_stmts_opt ::= c_suite_stmts
        c_suite_stmts_opt ::= suite_stmts_opt
        """

    def p_stmt(self, args):
        """
        pass ::=

        stmts_opt ::= stmts
        stmts_opt ::= pass

        stmts  ::= stmt+
        _stmts ::= stmts

        suite_stmts ::= _stmts
        suite_stmts ::= returns

        suite_stmts_opt ::= suite_stmts

        # passtmt is needed for semantic actions to add "pass"
        suite_stmts_opt ::= pass

        else_suite ::= suite_stmts
        else_suite ::= returns

        stmt ::= classdef
        stmt ::= call_stmt

        stmt ::= ifstmt
        stmt ::= if_or_stmt
        stmt ::= if_and_stmt
        stmt ::= ifelsestmt
        stmt ::= if_or_elsestmt
        stmt ::= if_or_not_elsestmt

        stmt ::= whilestmt
        stmt ::= while1stmt
        stmt ::= whileelsestmt
        stmt ::= while1elsestmt
        stmt ::= for
        stmt ::= forelsestmt
        stmt ::= try_except
        stmt ::= tryelsestmt
        stmt ::= tryfinallystmt
        stmt ::= last_stmt

        stmt ::= dict_comp_func

        for_iter       ::= _come_froms FOR_ITER
        dict_comp_func ::= BUILD_MAP_0 LOAD_FAST for_iter store
                           comp_iter JUMP_BACK RETURN_VALUE RETURN_LAST

        stmt ::= set_comp_func
        set_comp_func ::= BUILD_SET_0 LOAD_FAST for_iter store comp_iter
                          JUMP_BACK RETURN_VALUE RETURN_LAST

        set_comp_func ::= BUILD_SET_0 LOAD_FAST for_iter store comp_iter
                          COME_FROM JUMP_BACK RETURN_VALUE RETURN_LAST

        # last_stmt is a Python statement for which
        # end is a "return" or raise statement and
        # thefore may not have a COME_FROM after
        # it. It does *not* have to be the last stmt of
        # a list of stmts or c_stmts
        last_stmt  ::= forelselaststmt
        last_stmt  ::= iflaststmt

        stmt ::= del_stmt
        del_stmt ::= DELETE_FAST
        del_stmt ::= DELETE_NAME
        del_stmt ::= DELETE_GLOBAL

        stmt   ::= return

        # "returns" nonterminal is a sequence of statements that ends in a RETURN statement.
        # In later Python versions with jump optimization, this can cause JUMPs
        # that would normally appear to be omitted.

        returns ::= return
        returns ::= _stmts return

        stmt ::= genexpr_func
        genexpr_func ::= LOAD_FAST _come_froms FOR_ITER store comp_iter JUMP_BACK
        """
        pass

    def p_function_def(self, args):
        """
        stmt               ::= function_def
        function_def       ::= mkfunc store
        stmt               ::= function_def_deco
        function_def_deco  ::= mkfuncdeco store
        mkfuncdeco         ::= expr mkfuncdeco CALL_FUNCTION_1
        mkfuncdeco         ::= expr mkfuncdeco0 CALL_FUNCTION_1
        mkfuncdeco0        ::= mkfunc
        load_closure       ::= load_closure LOAD_CLOSURE
        load_closure       ::= LOAD_CLOSURE
        """

    def p_generator_exp3(self, args):
        """
        load_genexpr ::= LOAD_GENEXPR
        load_genexpr ::= BUILD_TUPLE_1 LOAD_GENEXPR LOAD_STR
        """

    def p_augmented_assign(self, args):
        """
        stmt ::= aug_assign1
        stmt ::= aug_assign2

        # This is odd in that other aug_assign1's have only 3 slots
        # The store isn't used as that's supposed to be also
        # indicated in the first expr
        aug_assign1 ::= expr expr
                        inplace_op store
        aug_assign1 ::= expr expr
                        inplace_op ROT_THREE STORE_SUBSCR
        aug_assign2 ::= expr DUP_TOP LOAD_ATTR expr
                        inplace_op ROT_TWO STORE_ATTR

        inplace_op ::= INPLACE_ADD
        inplace_op ::= INPLACE_SUBTRACT
        inplace_op ::= INPLACE_MULTIPLY
        inplace_op ::= INPLACE_TRUE_DIVIDE
        inplace_op ::= INPLACE_FLOOR_DIVIDE
        inplace_op ::= INPLACE_MODULO
        inplace_op ::= INPLACE_POWER
        inplace_op ::= INPLACE_LSHIFT
        inplace_op ::= INPLACE_RSHIFT
        inplace_op ::= INPLACE_AND
        inplace_op ::= INPLACE_XOR
        inplace_op ::= INPLACE_OR
        """

    def p_assign(self, args):
        """
        stmt ::= assign
        assign ::= expr DUP_TOP designList
        assign ::= expr store

        stmt ::= assign2
        stmt ::= assign3
        assign2 ::= expr expr ROT_TWO store store
        assign3 ::= expr expr expr ROT_THREE ROT_TWO store store store
        """

    def p_await(self, args):
        # Python 3.5+ Await things
        """
        expr       ::= await_expr
        await_expr ::= expr GET_AWAITABLE LOAD_CONST YIELD_FROM

        stmt       ::= await_stmt
        await_stmt ::= await_expr POP_TOP
        """

    def p_forstmt(self, args):
        """
        for_block   ::= c_stmts_opt COME_FROM_LOOP JUMP_BACK
        for_block   ::= c_stmts_opt _come_froms JUMP_BACK
        for_block   ::= c_stmts_opt come_from_loops JUMP_BACK
        for_block   ::= c_stmts
        for_block   ::= c_stmts JUMP_BACK

        forelsestmt ::= SETUP_LOOP expr get_for_iter store
                        for_block POP_BLOCK else_suite _come_froms

        forelselaststmt ::= SETUP_LOOP expr get_for_iter store
                for_block POP_BLOCK else_suitec _come_froms

        forelselaststmtc ::= SETUP_LOOP expr get_for_iter store
                for_block POP_BLOCK else_suitec _come_froms
        """


    def p_import20(self, args):
        """
        stmt ::= import
        stmt ::= import_from
        stmt ::= import_from_star
        stmt ::= importmultiple

        importlist ::= importlist alias
        importlist ::= alias
        alias      ::= IMPORT_NAME store
        alias      ::= IMPORT_FROM store
        alias      ::= IMPORT_NAME attributes store

        import           ::= LOAD_CONST LOAD_CONST alias
        import_from_star ::= LOAD_CONST LOAD_CONST IMPORT_NAME IMPORT_STAR
        import_from_star ::= LOAD_CONST LOAD_CONST IMPORT_NAME_ATTR IMPORT_STAR
        import_from      ::= LOAD_CONST LOAD_CONST IMPORT_NAME importlist POP_TOP
        importmultiple   ::= LOAD_CONST LOAD_CONST alias imports_cont

        imports_cont ::= import_cont+
        import_cont  ::= LOAD_CONST LOAD_CONST alias

        attributes   ::= LOAD_ATTR+
        """

    def p_import37(self, args):
        """
        stmt          ::= import_as37
        import_as37   ::= LOAD_CONST LOAD_CONST importlist37 store POP_TOP

        importlist37  ::= importlist37 ROT_TWO IMPORT_FROM
        importlist37  ::= importlist37 ROT_TWO POP_TOP IMPORT_FROM
        importlist37  ::= importattr37
        importattr37  ::= IMPORT_NAME_ATTR IMPORT_FROM

        # The 3.7base scanner adds IMPORT_NAME_ATTR
        alias         ::= IMPORT_NAME_ATTR attributes store
        alias         ::= IMPORT_NAME_ATTR store
        import_from   ::= LOAD_CONST LOAD_CONST importlist POP_TOP

        stmt          ::= import_from37
        importlist37  ::= importlist37 alias37
        importlist37  ::= alias37
        alias37       ::= IMPORT_NAME store
        alias37       ::= IMPORT_FROM store
        import_from37 ::= LOAD_CONST LOAD_CONST IMPORT_NAME_ATTR importlist37 POP_TOP

        """

    def p_list_comprehension(self, args):
        """
        expr ::= list_comp

        list_iter ::= list_for
        list_iter ::= list_if
        list_iter ::= list_if_not
        list_iter ::= lc_body

        lc_body   ::= expr LIST_APPEND
        list_for  ::= expr for_iter store list_iter jb_or_c
        list_comp ::= BUILD_LIST_0 list_iter

        list_if     ::= expr jump_if_false   list_iter
        list_if_not ::= expr jump_if_true    list_iter
        list_if     ::= expr jump_if_false37 list_iter
        list_if     ::= expr jump_if_false   list_iter COME_FROM
        list_if_not ::= expr jump_if_true    list_iter COME_FROM

        jump_if_false37 ::= POP_JUMP_IF_FALSE COME_FROM

        jb_or_c ::= JUMP_BACK
        jb_or_c ::= CONTINUE


        """

    def p_32on(self, args):
        """
        # Python < 3.5 no POP BLOCK
        whileTruestmt  ::= SETUP_LOOP c_stmts_opt JUMP_BACK COME_FROM_LOOP

        # Python 3.5+ has jump optimization to remove the redundant
        # jump_excepts. But in 3.3 we need them added

        except_handler ::= JUMP_FORWARD COME_FROM_EXCEPT except_stmts
                           END_FINALLY

        tryelsestmt    ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                           except_handler else_suite
                           jump_excepts come_from_except_clauses

        jump_excepts   ::= jump_except+

        kv3       ::= expr expr STORE_MAP
        """
        return

    def p_33on(self, args):
        """
        # Python 3.3+ adds yield from.
        expr          ::= yield_from
        yield_from    ::= expr GET_YIELD_FROM_ITER LOAD_CONST YIELD_FROM

        # Python 3.5+ has jump optimization to remove the redundant
        # jump_excepts. But in 3.3 we need them added

        try_except   ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                         except_handler
                         jump_excepts come_from_except_clauses
        c_try_except ::= SETUP_EXCEPT c_suite_stmts_opt POP_BLOCK
                         c_except_handler
                         jump_excepts come_from_except_clauses
        try_except  ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                        except_handler
                        jump_excepts come_from_except_clauses
        """

    def p_34on(self, args):
        """
        whilestmt     ::= setup_loop testexpr returns come_froms POP_BLOCK COME_FROM_LOOP

        # Seems to be needed starting 3.4.4 or so
        while1stmt    ::= setup_loop c_stmts
                          COME_FROM JUMP_BACK POP_BLOCK COME_FROM_LOOP
        while1stmt    ::= setup_loop c_stmts
                          POP_BLOCK COME_FROM_LOOP

        # FIXME the below masks a bug in not detecting COME_FROM_LOOP
        # grammar rules with COME_FROM -> COME_FROM_LOOP already exist
        whileelsestmt     ::= setup_loop testexpr c_stmts_opt JUMP_BACK POP_BLOCK
                              else_suitec COME_FROM

        while1elsestmt    ::= setup_loop c_stmts JUMP_BACK _come_froms POP_BLOCK else_suitec
                              COME_FROM_LOOP

        # Python 3.4+ optimizes the trailing two JUMPS away

        ifstmts_jump ::= stmts_opt JUMP_FORWARD JUMP_FORWARD _come_froms
        """

    def p_35on(self, args):
        """

        while1elsestmt ::= setup_loop c_stmts JUMP_BACK
                           POP_BLOCK else_suite COME_FROM_LOOP

        # The following rule is for Python 3.5+ where we can have stuff like
        # while ..
        #     if
        #     ...
        # the end of the "if" will jump back to the loop and there will be a COME_FROM
        # after the jump
        # c_stmts ::= lastc_stmt come_froms c_stmts

        inplace_op ::= INPLACE_MATRIX_MULTIPLY
        binary_operator  ::= BINARY_MATRIX_MULTIPLY

        # Python 3.5+ does jump optimization
        # In <.3.5 the below is a "JUMP_FORWARD" to a "jump".

        ret_expr ::= expr
        ret_expr ::= ret_and
        ret_expr ::= ret_or

        return_if_stmt ::= ret_expr RETURN_END_IF POP_BLOCK

        jb_cf     ::= JUMP_BACK COME_FROM
        ifelsestmtc ::= testexpr c_stmts_opt JUMP_FORWARD else_suitec
        ifelsestmtc ::= testexpr c_stmts_opt jb_cf else_suitec come_from_opt

        # We want to keep the positions of the "then" and
        # "else" statements in "ifelstmtl" similar to others of this ilk.
        testexpr_cf ::= testexpr come_froms

        ifelsestmtc ::= testexpr_cf c_stmts_opt jb_cf else_suitec
        iflaststmt  ::= testexpr stmts_opt JUMP_FORWARD
        """

    def p_37async(self, args):
        """
        stmt     ::= async_for_stmt37
        stmt     ::= async_for_stmt
        stmt     ::= async_forelse_stmt

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

        async_for_stmt     ::= setup_loop expr
                               GET_AITER
                               LOAD_CONST YIELD_FROM SETUP_EXCEPT GET_ANEXT LOAD_CONST
                               YIELD_FROM
                               store
                               POP_BLOCK JUMP_FORWARD COME_FROM_EXCEPT DUP_TOP
                               LOAD_GLOBAL COMPARE_OP POP_JUMP_IF_FALSE
                               POP_TOP POP_TOP POP_TOP POP_EXCEPT POP_BLOCK
                               JUMP_ABSOLUTE END_FINALLY COME_FROM
                               for_block POP_BLOCK
                               COME_FROM_LOOP

        # Order of LOAD_CONST YIELD_FROM is switched from 3.6 to save a LOAD_CONST
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
        """

    def p_grammar(self, args):
        """
        sstmt ::= stmt
        sstmt ::= ifelsestmtr
        sstmt ::= return RETURN_LAST

        return_if_stmts ::= return_if_stmt come_from_opt
        return_if_stmts ::= _stmts return_if_stmt _come_froms
        return_if_stmt  ::= ret_expr RETURN_END_IF
        returns         ::= _stmts return_if_stmt


        break     ::= BREAK_LOOP
        continue  ::= CONTINUE
        continues ::= _stmts lastc_stmt continue
        continues ::= lastc_stmt continue
        continues ::= continue


        kwarg      ::= LOAD_STR expr
        kwargs     ::= kwarg+

        classdef ::= build_class store

        # FIXME: we need to add these because don't detect this properly
        # in custom rules. Specifically if one of the exprs is CALL_FUNCTION
        # then we'll mistake that for the final CALL_FUNCTION.
        # We can fix by triggering on the CALL_FUNCTION op
        # Python3 introduced LOAD_BUILD_CLASS
        # Other definitions are in a custom rule
        build_class ::= LOAD_BUILD_CLASS mkfunc expr call CALL_FUNCTION_3
        build_class ::= LOAD_BUILD_CLASS mkfunc expr call expr CALL_FUNCTION_4

        stmt ::= classdefdeco
        classdefdeco ::= classdefdeco1 store

        # In 3.7 there are some LOAD_GLOBALs we don't convert to LOAD_ASSERT
        stmt    ::= assert2
        assert2 ::= expr jump_if_true LOAD_GLOBAL expr CALL_FUNCTION_1 RAISE_VARARGS_1

        # "assert_invert" tests on the negative of the condition given
        stmt          ::= assert_invert
        assert_invert ::= testtrue LOAD_GLOBAL RAISE_VARARGS_1

        expr    ::= LOAD_ASSERT

        pop_jump    ::= POP_JUMP_IF_TRUE
        pop_jump    ::= POP_JUMP_IF_FALSE

        ifstmt      ::= testexpr ifstmts_jump _come_froms
        if_or_stmt  ::= expr POP_JUMP_IF_TRUE expr pop_jump come_froms
                        stmts COME_FROM
        if_and_stmt ::= expr POP_JUMP_IF_FALSE expr COME_FROM
                        stmts _come_froms

        if_and_elsestmtc    ::= expr POP_JUMP_IF_FALSE
                                expr POP_JUMP_IF_FALSE
                                c_stmts jb_cfs else_suitec opt_come_from_except
        if_or_elsestmt      ::= expr jump_if_true
                                come_from_opt expr POP_JUMP_IF_FALSE come_froms
                                stmts jf_cfs else_suite opt_come_from_except
        if_or_not_elsestmt  ::= expr jump_if_true
                                come_from_opt expr POP_JUMP_IF_TRUE come_froms
                                stmts jf_cfs else_suite opt_come_from_except

        testexpr   ::= testfalse
        testexpr   ::= testtrue
        testfalse  ::= expr jump_if_false

        testtrue   ::= expr jump_if_true
        testtruec  ::= expr jump_if_true
        testtrue   ::= compare_chained37

        testfalse  ::= and_not
        testfalse  ::= compare_chained37_false

        ifstmts_jump ::= return_if_stmts
        ifstmts_jump ::= stmts_opt come_froms
        ifstmts_jump ::= COME_FROM stmts COME_FROM

        iflaststmt  ::= testexpr stmts
        iflaststmt  ::= testexpr stmts JUMP_FORWARD

        iflaststmtc ::= testexpr c_stmts
        iflaststmtc ::= testexpr c_stmts JUMP_BACK
        iflaststmtc ::= testexpr c_stmts JUMP_BACK COME_FROM_LOOP
        iflaststmtc ::= testexpr c_stmts JUMP_BACK POP_BLOCK

        # c_stmts might terminate, or have "continue" so no JUMP_BACK.
        # But if that's true, the "testexpr" needs still to jump to the "COME_FROM'
        iflaststmtc ::= testexpr c_stmts COME_FROM

        # Note: in if/else kinds of statements, we err on the side
        # of missing "else" clauses. Therefore we include grammar
        # rules with and without ELSE.

        ifelsestmt    ::= testexpr
                          stmts_opt jf_cfs else_suite opt_come_from_except
        ifelsestmt    ::= testexpr stmts_opt JUMP_FORWARD
                          else_suite opt_come_from_except

        ifelsestmtc ::= testexpr
                        c_stmts_opt jump_forward_else
                        else_suitec opt_come_from_except
        ifelsestmtc ::= testexpr
                        c_stmts_opt cf_jump_back
                        else_suitec

        # This handles the case where a "JUMP_ABSOLUTE" is part
        # of an inner if in c_stmts_opt
        ifelsestmtc ::= testexpr c_stmts come_froms
                        else_suite


        ifelsestmtr ::= testexpr return_if_stmts returns


        cf_jump_back ::= COME_FROM JUMP_BACK

        # FIXME: this feels like a hack. Is it just 1 or two
        # COME_FROMs?  the parsed tree for this and even with just the
        # one COME_FROM for Python 2.7 seems to associate the
        # COME_FROM targets from the wrong places

        # this is nested inside a try_except
        tryfinallystmt ::= SETUP_FINALLY suite_stmts_opt
                           POP_BLOCK LOAD_CONST
                           COME_FROM_FINALLY suite_stmts_opt END_FINALLY

        except_handler ::= jmp_abs COME_FROM except_stmts
                           _come_froms END_FINALLY
        except_handler ::= jmp_abs COME_FROM_EXCEPT except_stmts
                           _come_froms END_FINALLY

        c_except_handler ::= jmp_abs COME_FROM c_except_stmts
                           _come_froms END_FINALLY
        c_except_handler ::= jmp_abs COME_FROM_EXCEPT c_except_stmts
                           _come_froms END_FINALLY
        c_except_handler ::= jmp_abs COME_FROM_EXCEPT c_except_stmts

        try_except   ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                         except_handler
                         jump_excepts come_from_except_clauses
        c_try_except ::= SETUP_EXCEPT c_suite_stmts_opt POP_BLOCK
                         c_except_handler
                         jump_excepts come_from_except_clauses
        # FIXME: remove this
        except_handler ::= JUMP_FORWARD COME_FROM except_stmts
                           come_froms END_FINALLY come_from_opt

        except_stmts   ::= except_stmt+

        except_stmt    ::= except_cond1 except_suite come_from_opt
        except_stmt    ::= except_cond2 except_suite come_from_opt
        except_stmt    ::= except_cond2 except_suite_finalize
        except_stmt    ::= except
        except_stmt    ::= stmt

        c_except_stmts ::= except_stmts
        c_except_stmts ::= c_except_stmt+
        c_except_stmt  ::= c_stmt
        c_except_stmt  ::= stmt

        ## FIXME: what's except_pop_except?
        except_stmt    ::= except_pop_except

        # Python3 introduced POP_EXCEPT
        except_suite ::= c_stmts_opt POP_EXCEPT jump_except
        jump_except ::= JUMP_ABSOLUTE
        jump_except ::= JUMP_BACK
        jump_except ::= JUMP_FORWARD
        jump_except ::= CONTINUE

        # This is used in Python 3 in
        # "except ... as e" to remove 'e' after the c_stmts_opt finishes
        except_suite_finalize ::= SETUP_FINALLY c_stmts_opt except_var_finalize
                                  END_FINALLY jump

        except_suite_finalize ::= SETUP_FINALLY c_stmts_opt except_var_finalize
                                  END_FINALLY POP_EXCEPT jump

        except_var_finalize ::= POP_BLOCK POP_EXCEPT LOAD_CONST COME_FROM_FINALLY
                                LOAD_CONST store del_stmt
        except_var_finalize ::= POP_BLOCK            LOAD_CONST COME_FROM_FINALLY
                                LOAD_CONST store del_stmt

        except_suite ::= returns

        except_cond1 ::= DUP_TOP expr COMPARE_OP
                         jump_if_false POP_TOP POP_TOP POP_TOP

        except_cond2 ::= DUP_TOP expr COMPARE_OP
                         jump_if_false POP_TOP store POP_TOP come_from_opt

        except  ::=  POP_TOP POP_TOP POP_TOP c_stmts_opt POP_EXCEPT jump
        except  ::=  POP_TOP POP_TOP POP_TOP returns

        jmp_abs ::= JUMP_ABSOLUTE
        jmp_abs ::= JUMP_BACK
        jmp_abs ::= JUMP_FORWARD

        """

    def p_misc3(self, args):
        """
        except_handler ::= JUMP_FORWARD COME_FROM_EXCEPT except_stmts
                           come_froms END_FINALLY

        c_except_handler ::= jmp_abs COME_FROM c_except_stmts
                           _come_froms END_FINALLY
        c_except_handler ::= jmp_abs COME_FROM_EXCEPT c_except_stmts
                           _come_froms END_FINALLY
        c_except_handler ::= jmp_abs COME_FROM_EXCEPT c_except_stmts
        """

    def p_come_from3(self, args):
        """
        opt_come_from_except ::= COME_FROM_EXCEPT
        opt_come_from_except ::= _come_froms
        opt_come_from_except ::= come_from_except_clauses

        come_from_except_clauses ::= COME_FROM_EXCEPT_CLAUSE+
        """

    def p_jump3(self, args):
        """
        # FIXME: Common with 2.7
        ret_expr_or_cond ::= ret_expr
        ret_expr_or_cond ::= if_exp_ret

        ret_and    ::= expr JUMP_IF_FALSE_OR_POP ret_expr_or_cond COME_FROM
        ret_or     ::= expr JUMP_IF_TRUE_OR_POP ret_expr_or_cond COME_FROM
        if_exp_ret ::= expr POP_JUMP_IF_FALSE expr RETURN_END_IF COME_FROM ret_expr_or_cond

        testfalse_not_or   ::= expr jump_if_false expr jump_if_false COME_FROM
        testfalse_not_and ::= and jump_if_true come_froms

        testfalse_not_and ::= expr jump_if_false expr jump_if_true  COME_FROM
        testfalse ::= testfalse_not_or
        testfalse ::= testfalse_not_and
        testfalse ::= or jump_if_false COME_FROM

        iflaststmtc ::= testexprc c_stmts JUMP_BACK
        iflaststmtc ::= testexprc c_stmts JUMP_BACK COME_FROM_LOOP
        iflaststmtc ::= testexprc c_stmts JUMP_BACK POP_BLOCK

        testexprc   ::= testtruec
        testexprc   ::= testfalsec
        testfalsec  ::= expr jump_if_true

        """

    def p_stmt3(self, args):
        """
        # If statement inside a loop:
        c_stmt             ::= ifstmtc
        c_stmt             ::= if_and_elsestmtc
        c_stmt             ::= assign

        if_exp_lambda      ::= expr jump_if_false expr return_if_lambda
                               return_stmt_lambda
        if_exp_not_lambda
                           ::= expr jump_if_true expr return_if_lambda
                               return_stmt_lambda
        return_stmt_lambda ::= ret_expr RETURN_VALUE_LAMBDA

        stmt               ::= return_closure
        return_closure     ::= LOAD_CLOSURE RETURN_VALUE RETURN_LAST

        stmt               ::= whileTruestmt
        ifelsestmt         ::= testexpr stmts_opt JUMP_FORWARD else_suite _come_froms
        ifelsestmtc        ::= testexpr c_stmts_opt JUMP_FORWARD else_suite _come_froms

        ifstmtc            ::= testexpr ifstmts_jumpc
        ifstmtc            ::= testexprc ifstmts_jumpc

        ifstmts_jumpc             ::= ifstmts_jump
        ifstmts_jumpc             ::= c_stmts_opt come_froms
        ifstmts_jumpc             ::= COME_FROM c_stmts come_froms
        ifstmts_jumpc             ::= c_stmts JUMP_BACK

        ifstmts_jump              ::= stmts come_froms
        ifstmts_jump              ::= COME_FROM stmts come_froms


        # The following can happen when the jump offset is large and
        # Python is looking to do a small jump to a larger jump to get
        # around the problem that the offset can't be represented in
        # the size allowed for the jump offset. This is more likely to
        # happen in wordcode Python since the offset range has been
        # reduced.  FIXME: We should add a reduction check that the
        # final jump goes to another jump.

        ifstmts_jumpc     ::= COME_FROM c_stmts JUMP_BACK
        ifstmts_jumpc     ::= COME_FROM c_stmts JUMP_FORWARD

        """

    def p_loop_stmt3(self, args):
        """
        setup_loop        ::= SETUP_LOOP _come_froms
        for               ::= setup_loop expr get_for_iter store for_block
                              POP_BLOCK
        for               ::= setup_loop expr get_for_iter store for_block
                              POP_BLOCK COME_FROM_LOOP

        forelsestmt       ::= setup_loop expr get_for_iter store for_block POP_BLOCK else_suitec
        forelsestmt       ::= setup_loop expr get_for_iter store for_block POP_BLOCK else_suite
                              COME_FROM_LOOP

        forelselaststmt   ::= setup_loop expr get_for_iter store for_block POP_BLOCK else_suitec
                              COME_FROM_LOOP

        whilestmt         ::= setup_loop testexpr c_stmts_opt COME_FROM JUMP_BACK POP_BLOCK
                              COME_FROM_LOOP


        whilestmt         ::= setup_loop testexpr c_stmts_opt JUMP_BACK POP_BLOCK
                              COME_FROM_LOOP

        whilestmt         ::= setup_loop testexpr returns          POP_BLOCK
                              COME_FROM_LOOP

        # We can be missing a COME_FROM_LOOP if the "while" statement is nested inside an if/else
        # so after the POP_BLOCK we have a JUMP_FORWARD which forms the "else" portion of the "if"
        # This is undoubtedly some sort of JUMP optimization going on.
        # We have a reduction check for this peculiar case.

        whilestmt         ::= setup_loop testexpr c_stmts_opt JUMP_BACK come_froms
                              POP_BLOCK

        while1elsestmt    ::= setup_loop          c_stmts     JUMP_BACK
                              else_suitec

        whileelsestmt     ::= setup_loop testexpr c_stmts_opt JUMP_BACK POP_BLOCK
                              else_suitec COME_FROM_LOOP

        whileTruestmt     ::= setup_loop c_stmts_opt          JUMP_BACK POP_BLOCK
                              _come_froms

        # FIXME: Python 3.? starts adding branch optimization? Put this starting there.

        while1stmt        ::= setup_loop c_stmts COME_FROM_LOOP
        while1stmt        ::= setup_loop c_stmts COME_FROM_LOOP JUMP_BACK POP_BLOCK COME_FROM_LOOP
        while1stmt        ::= setup_loop c_stmts COME_FROM JUMP_BACK COME_FROM_LOOP

        while1elsestmt    ::= setup_loop c_stmts JUMP_BACK
                              else_suite COME_FROM_LOOP
        # FIXME: investigate - can code really produce a NOP?
        for               ::= setup_loop expr get_for_iter store for_block POP_BLOCK NOP
                              COME_FROM_LOOP
        """

    def p_36misc(self, args):
        """
        sstmt ::= sstmt RETURN_LAST

        # 3.6 redoes how return_closure works. FIXME: Isolate to LOAD_CLOSURE
        return_closure   ::= LOAD_CLOSURE DUP_TOP STORE_NAME RETURN_VALUE RETURN_LAST

        for_block       ::= c_stmts_opt come_from_loops JUMP_BACK
        come_from_loops ::= COME_FROM_LOOP*

        whilestmt       ::= setup_loop testexpr c_stmts_opt
                            JUMP_BACK come_froms POP_BLOCK COME_FROM_LOOP
        whilestmt       ::= setup_loop testexpr c_stmts_opt
                            come_froms JUMP_BACK come_froms POP_BLOCK COME_FROM_LOOP

        # 3.6 due to jump optimization, we sometimes add RETURN_END_IF where
        # RETURN_VALUE is meant. Specifcally this can happen in
        # ifelsestmt -> ...else_suite _. suite_stmts... (last) stmt
        return ::= ret_expr RETURN_END_IF
        return ::= ret_expr RETURN_VALUE

        jf_cf        ::= JUMP_FORWARD COME_FROM

        if_exp       ::= expr jump_if_false expr jf_cf expr COME_FROM

        except_suite ::= c_stmts_opt COME_FROM POP_EXCEPT jump_except COME_FROM

        jb_cfs      ::= come_from_opt JUMP_BACK come_froms
        ifelsestmtc ::= testexpr c_stmts_opt jb_cfs else_suitec

        # In 3.6+, A sequence of statements ending in a RETURN can cause
        # JUMP_FORWARD END_FINALLY to be omitted from try middle

        except_return    ::= POP_TOP POP_TOP POP_TOP returns
        except_handler   ::= JUMP_FORWARD COME_FROM_EXCEPT except_return

        # Try middle following a returns
        except_handler36 ::= COME_FROM_EXCEPT except_stmts END_FINALLY

        stmt             ::= try_except36
        try_except36     ::= SETUP_EXCEPT returns except_handler36
                             opt_come_from_except
        try_except36     ::= SETUP_EXCEPT suite_stmts
        try_except36     ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                             except_handler36 come_from_opt

        # 3.6 omits END_FINALLY sometimes
        except_handler36 ::= COME_FROM_EXCEPT except_stmts
        except_handler36 ::= JUMP_FORWARD COME_FROM_EXCEPT except_stmts
        except_handler   ::= jmp_abs COME_FROM_EXCEPT except_stmts

        stmt             ::= tryfinally36
        tryfinally36     ::= SETUP_FINALLY returns
                             COME_FROM_FINALLY suite_stmts
        tryfinally36     ::= SETUP_FINALLY returns
                             COME_FROM_FINALLY suite_stmts_opt END_FINALLY
        except_suite_finalize ::= SETUP_FINALLY returns
                                  COME_FROM_FINALLY suite_stmts_opt END_FINALLY jump

        stmt ::= tryfinally_return_stmt1
        stmt ::= tryfinally_return_stmt2
        tryfinally_return_stmt1 ::= SETUP_FINALLY suite_stmts_opt POP_BLOCK LOAD_CONST
                                    COME_FROM_FINALLY returns
        tryfinally_return_stmt2 ::= SETUP_FINALLY suite_stmts_opt POP_BLOCK LOAD_CONST
                                    COME_FROM_FINALLY

        compare_chained2 ::= expr COMPARE_OP come_froms JUMP_FORWARD
        """


def info(args):
    # Check grammar
    p = Python37Parser()
    if len(args) > 0:
        arg = args[0]
        if arg == "3.7":
            from decompyle3.parser.parse37 import Python37Parser

            p = Python37Parser()
        elif arg == "3.8":
            from decompyle3.parser.parse38 import Python38Parser

            p = Python38Parser()
        else:
            raise RuntimeError("Only 3.7 and 3.8 supported")
    p.check_grammar()
    if len(sys.argv) > 1 and sys.argv[1] == "dump":
        print("-" * 50)
        p.dump_grammar()


class Python37ParserSingle(Python37Parser, PythonParserSingle):
    # FIXME: add a suitable __init__
    pass


if __name__ == "__main__":
    # Check grammar
    from decompyle3.parsers.dump import dump_and_check
    p = Python37Parser()
    modified_tokens = set(
        """JUMP_BACK CONTINUE RETURN_END_IF COME_FROM
           LOAD_GENEXPR LOAD_ASSERT LOAD_SETCOMP LOAD_DICTCOMP LOAD_CLASSNAME
           LAMBDA_MARKER RETURN_LAST
        """.split()
    )

    dump_and_check(p, 3.7, modified_tokens)
