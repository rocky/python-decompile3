#  Copyright (c) 2017-2023 Rocky Bernstein
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
Python 3.7 lambda grammar for the spark Earley-algorithm parser.
"""

from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG

from decompyle3.parsers.p37.lambda_custom import Python37LambdaCustom
from decompyle3.parsers.parse_heads import PythonBaseParser, PythonParserLambda


class Python37LambdaParser(Python37LambdaCustom, PythonParserLambda):
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
        Python37LambdaCustom.__init__(self)

    def customize_grammar_rules(self, tokens, customize):
        self.customize_grammar_rules_lambda37(tokens, customize)

    ###################################################
    #  Python 3.7 grammar rules for lambda expressions
    ###################################################
    pass

    def p_lambda(self, args):
        """
        lambda_start       ::= return_expr_lambda LAMBDA_MARKER

        return_expr_lambda ::= expr RETURN_VALUE_LAMBDA
        return_expr_lambda ::= genexpr_func LOAD_CONST RETURN_VALUE_LAMBDA
        return_expr_lambda ::= if_exp_lambda
        return_expr_lambda ::= if_exp_lambda2
        return_expr_lambda ::= if_exp_not_lambda
        return_expr_lambda ::= if_exp_not_lambda2
        return_expr_lambda ::= if_exp_dead_code
        return_expr_lambda ::= dict_comp_func

        ## FIXME: add rules for these
        # return_expr_lambda ::= generator_exp
        # return_expr_lambda ::= list_comp_func

        return_expr_lambda ::= set_comp_func


        return_if_lambda   ::= RETURN_END_IF_LAMBDA COME_FROM
        return_if_lambda   ::= RETURN_END_IF_LAMBDA

        if_exp_lambda      ::= expr_pjif expr return_if_lambda
                               return_expr_lambda LAMBDA_MARKER
        if_exp_lambda2     ::= and_parts return_expr_lambda come_froms
                               return_expr_lambda opt_lambda_marker
        if_exp_not_lambda  ::= expr POP_JUMP_IF_TRUE expr return_if_lambda
                               return_expr_lambda LAMBDA_MARKER
        if_exp_not_lambda2 ::= expr POP_JUMP_IF_TRUE expr
                               RETURN_VALUE_LAMBDA COME_FROM return_expr_lambda
        if_exp_dead_code   ::= return_expr_lambda return_expr_lambda
        opt_lambda_marker  ::= LAMBDA_MARKER?
        """

    def p_and_or_not(self, args):
        """
        # Note: reduction-rule checks are needed for many of the below;
        # the rules in of themselves are not sufficient.

        # Nonterminals that end in "_cond" are used in "conditions":
        # used for testing in control structures where the test is important and
        # the value popped. Conditions also generally have non-local COME_FROMs
        # that often need to be checked in the control structure. This is for example
        # how we determine the difference between some "if not (not a or b) versus
        # "if a and b".

        # FIXME: this is some sort of bool_not or not_cond. Figure out how to have
        # it not appear in arbitrary expr's
        not        ::= expr_pjit

        and_parts  ::= expr_pjif+

        # Note: "and" like "nor" might not have a trailing "come_from".
        #       "nand" and "or", in contrast, *must* have at least one "come_from".
        not_or       ::= and_parts expr_pjif _come_froms

        and_cond     ::= and_parts expr_pjif _come_froms
        and_cond     ::= testfalse expr_pjif _come_froms
        and_not_cond ::= and_not

        # FIXME: Investigate - We don't do the below because these rules prevent the
        # "and_cond" from triggering.

        # and      ::= and_parts expr
        # and      ::= not expr

        nand       ::= and_parts expr_pjit  come_froms
        c_nand     ::= and_parts expr_pjitt come_froms

        or_parts  ::= expr_pjit+

        # Note: "nor" like "and" might not have a trailing "come_from".
        #       "nand" and "or_cond", in contrast, *must* have at least one "come_from".
        or_cond     ::= or_parts expr_pjif come_froms
        or_cond     ::= not_and_not expr_pjif come_froms
        or_cond1    ::= and POP_JUMP_IF_TRUE come_froms expr_pjif come_from_opt

        nor_cond    ::= or_parts expr_pjif

        # When we alternating and/or's such as:
        #    a and (b or c) and d
        # instead of POP_JUMP_IF_TRUE, JUMP_IF_FALSE_OR_POP is sometimes be used
        # The semantic rules for "and" require expr-like things in positions 0 and 1,
        # thus the use of expr_jifop_cfs below.

        expr_jifop_cfs ::= expr JUMP_IF_FALSE_OR_POP _come_froms
        and            ::= expr_jifop_cfs expr _come_froms

        or_and         ::= expr_jitop expr come_from_opt JUMP_IF_FALSE_OR_POP expr
                           _come_froms
        or_and1        ::= or_parts and_parts come_froms
        and_or         ::= expr_jifop expr come_from_opt JUMP_IF_TRUE_OR_POP expr
                          _come_froms

        ## A COME_FROM is dropped off because of JUMP-to-JUMP optimization
        # and       ::= expr_pjif expr

        ## Note that "POP_JUMP_IF_FALSE" is what we check on in the "and" reduce rule.
        # and       ::= expr_pjif expr COME_FROM

        jump_if_false_cf ::= POP_JUMP_IF_FALSE COME_FROM
        and_or_cond      ::= and_parts expr POP_JUMP_IF_TRUE come_froms expr_pjif
                             _come_froms

        # For "or", keep index 0 and 1 be the two expressions.

        or        ::= or_parts   expr
        or        ::= expr_pjit  expr COME_FROM
        or        ::= expr_pjit  expr jump_if_false_cf

        # Note: in the "or below", if "come_from_opt" becomes
        # _come_froms, then we will need to write a check to make sure
        # *all* of the COME_FROMs are associated with the
        # "or".
        #
        # Otherwise, in 3.8 we may turn:
        #     i and j or k # i == i and (j or k)
        #  erroneously into:
        #     i and (j or k)

        or        ::= expr_jitop expr come_from_opt
        or_expr   ::= expr JUMP_IF_TRUE expr COME_FROM

        jitop_come_from_expr ::= JUMP_IF_TRUE_OR_POP _come_froms expr
        and_or_expr  ::= and_parts expr jitop_come_from_expr COME_FROM
        """

    def p_come_froms(self, args):
        """
        # Zero or one COME_FROM
        # And/or expressions have this
        come_from_opt ::= COME_FROM?

        # One or more COME_FROMs - joins of tryelse's have this
        come_froms    ::= COME_FROM+

        # Zero or more COME_FROMs - loops can have this
        _come_froms   ::= COME_FROM*
        _come_froms   ::= COME_FROM_LOOP
        """

    def p_jump(self, args):
        """
        jump               ::= JUMP_FORWARD
        jump               ::= JUMP_LOOP
        jump_or_break      ::= jump
        jump_or_break      ::= BREAK_LOOP

        # These are used to keep parse tree indices the same
        # in "if"/"else" like rules.
        jump_forward_else  ::= JUMP_FORWARD _come_froms
        jump_forward_else  ::= come_froms jump COME_FROM

        pjump_ift          ::= POP_JUMP_IF_TRUE
        pjump_ift          ::= POP_JUMP_IF_TRUE_LOOP

        pjump_iff          ::= POP_JUMP_IF_FALSE
        pjump_iff          ::= POP_JUMP_IF_FALSE_LOOP

        # pjump              ::= pjump_iff
        # pjump              ::= pjump_ift
        """

    def p_37chained(self, args):
        """
        # A compare_chained is two comparisons like x <= y <= z
        compare_chained     ::= expr compare_chained_middle ROT_TWO POP_TOP _come_froms
        compare_chained     ::= compare_chained37
        compare_chained     ::= compare_chained37_false

        compare_chained_and ::= expr chained_parts
                                compare_chained_righta_false_37
                                come_froms
                                POP_TOP JUMP_FORWARD COME_FROM
                                negated_testtrue
                                come_froms

        # We don't use testtrue directly because we need to tell the semantic
        # action to negate the testtrue
        negated_testtrue ::= testtrue


        c_compare_chained   ::= c_compare_chained37_false

        compare_chained37   ::= expr chained_parts
        compare_chained37   ::= expr compare_chained_middlea_37
        compare_chained37   ::= expr compare_chained_middlec_37
        c_compare_chained37   ::= expr c_compare_chained_middlea_37
        # c_compare_chained37   ::= expr c_compare_chained_middlec_37

        compare_chained37_false   ::= expr compare_chained_middle_false_37
        compare_chained37_false   ::= expr compare_chained_middleb_false_37
        compare_chained37_false   ::= expr compare_chained_right_false_37

        c_compare_chained37_false ::= expr c_compare_chained_right_false_37
        c_compare_chained37_false ::= expr c_compare_chained_middleb_false_37
        c_compare_chained37_false ::= compare_chained37_false

        compare_chained_middle     ::= expr DUP_TOP ROT_THREE COMPARE_OP
                                       JUMP_IF_FALSE_OR_POP compare_chained_middle
                                       COME_FROM
        compare_chained_middle     ::= expr DUP_TOP ROT_THREE COMPARE_OP
                                       JUMP_IF_FALSE_OR_POP compare_chained_right
                                       COME_FROM

        chained_parts              ::= chained_part+

        chained_part               ::= expr DUP_TOP ROT_THREE COMPARE_OP come_from_opt
                                       POP_JUMP_IF_FALSE

        chained_part               ::= expr DUP_TOP ROT_THREE COMPARE_OP come_from_opt

        # c_chained_parts            ::= c_chained_part+
        # c_chained_part             ::= expr DUP_TOP ROT_THREE COMPARE_OP come_from_opt
                                         POP_JUMP_IF_FALSE_LOOP
        # c_chained_parts            ::= chained_parts


        compare_chained_middlea_37       ::= chained_parts
                                       compare_chained_righta_37 COME_FROM
                                       POP_TOP come_from_opt
        c_compare_chained_middlea_37     ::= chained_parts
                                       c_compare_chained_righta_37 COME_FROM
                                       POP_TOP come_from_opt

        compare_chained_middleb_false_37 ::= chained_parts
                                       compare_chained_rightb_false_37
                                       POP_TOP jump _come_froms

        c_compare_chained_middleb_false_37 ::= chained_parts
                                         c_compare_chained_rightb_false_37 POP_TOP jump
                                         _come_froms
        c_compare_chained_middleb_false_37 ::= chained_parts
                                         compare_chained_rightb_false_37 POP_TOP jump
                                         _come_froms

        compare_chained_middlec_37       ::= chained_parts
                                             compare_chained_righta_37 POP_TOP

        compare_chained_middle_false_37  ::= chained_parts
                                             compare_chained_rightc_37 POP_TOP JUMP_FORWARD
                                             come_from_opt
        compare_chained_middle_false_37  ::= chained_parts
                                             compare_chained_rightb_false_37 POP_TOP jump
                                             COME_FROM

        compare_chained_right           ::= expr COMPARE_OP JUMP_FORWARD
        compare_chained_right           ::= expr COMPARE_OP RETURN_VALUE
        compare_chained_right           ::= expr COMPARE_OP RETURN_VALUE_LAMBDA

        compare_chained_right_false_37  ::= chained_parts
                                            compare_chained_righta_false_37 POP_TOP
                                            JUMP_LOOP COME_FROM
        c_compare_chained_right_false_37 ::= chained_parts
                                             c_compare_chained_righta_false_37 POP_TOP
                                             JUMP_LOOP COME_FROM

        compare_chained_righta_37       ::= expr COMPARE_OP come_from_opt
                                            POP_JUMP_IF_TRUE JUMP_FORWARD
        c_compare_chained_righta_37     ::= expr COMPARE_OP come_from_opt
                                            POP_JUMP_IF_TRUE_LOOP JUMP_FORWARD


        compare_chained_righta_37       ::= expr COMPARE_OP come_from_opt
                                            POP_JUMP_IF_TRUE JUMP_LOOP
        compare_chained_righta_false_37 ::= expr COMPARE_OP come_from_opt
                                            POP_JUMP_IF_FALSE jf_cfs


        compare_chained_rightb_false_37   ::= expr COMPARE_OP come_from_opt
                                              POP_JUMP_IF_FALSE
                                              jump_or_break COME_FROM
        c_compare_chained_rightb_false_37 ::= expr COMPARE_OP come_from_opt
                                              POP_JUMP_IF_FALSE_LOOP jump_or_break
                                              COME_FROM
        c_compare_chained_righta_false_37 ::= expr COMPARE_OP come_from_opt
                                              POP_JUMP_IF_FALSE_LOOP jf_cfs
        c_compare_chained_righta_false_37 ::= expr COMPARE_OP come_from_opt
                                              POP_JUMP_IF_FALSE_LOOP
        c_compare_chained_rightb_false_37 ::= expr COMPARE_OP come_from_opt
                                              JUMP_FORWARD COME_FROM


        compare_chained_rightc_37          ::= chained_parts
                                               compare_chained_righta_false_37
        """

    def p_expr(self, args):
        """
        expr ::= LOAD_CODE
        expr ::= LOAD_CONST
        expr ::= LOAD_DEREF
        expr ::= LOAD_FAST
        expr ::= LOAD_GLOBAL
        expr ::= LOAD_NAME
        expr ::= LOAD_STR

        expr ::= and
        expr ::= and_or
        expr ::= and_or_expr
        expr ::= attribute37
        expr ::= bin_op
        expr ::= call
        expr ::= compare
        expr ::= genexpr_func
        expr ::= if_exp
        expr ::= if_exp_loop
        expr ::= list_comp
        expr ::= not
        expr ::= or
        expr ::= or_and
        expr ::= or_expr
        expr ::= set_comp
        expr ::= subscript
        expr ::= subscript2
        expr ::= unary_not
        expr ::= unary_op
        expr ::= yield

        # Python 3.3+ adds yield from.
        expr          ::= yield_from
        yield_from    ::= expr GET_YIELD_FROM_ITER LOAD_CONST YIELD_FROM

        attribute37       ::= expr LOAD_METHOD

        # bin_op (formerly "binary_expr") is the Python AST BinOp
        bin_op            ::= expr expr binary_operator

        binary_operator   ::= BINARY_ADD
        binary_operator   ::= BINARY_AND
        binary_operator   ::= BINARY_FLOOR_DIVIDE
        binary_operator   ::= BINARY_LSHIFT
        binary_operator   ::= BINARY_MATRIX_MULTIPLY
        binary_operator   ::= BINARY_MODULO
        binary_operator   ::= BINARY_MULTIPLY
        binary_operator   ::= BINARY_OR
        binary_operator   ::= BINARY_POWER
        binary_operator   ::= BINARY_RSHIFT
        binary_operator   ::= BINARY_SUBTRACT
        binary_operator   ::= BINARY_TRUE_DIVIDE
        binary_operator   ::= BINARY_XOR

        # FIXME: the below is to work around test_grammar expecting a "call" to be
        # on the LHS because it is also somewhere on in a rule.
        call              ::= expr CALL_METHOD_0

        compare           ::= compare_chained
        compare           ::= compare_single
        compare_single    ::= expr expr COMPARE_OP
        c_compare         ::= c_compare_chained

        genexpr_func      ::= LOAD_ARG _come_froms FOR_ITER store comp_iter
                              _come_froms JUMP_LOOP _come_froms

        load_genexpr      ::= LOAD_GENEXPR
        load_genexpr      ::= BUILD_TUPLE_1 LOAD_GENEXPR LOAD_STR

        subscript         ::= expr expr BINARY_SUBSCR
        subscript2        ::= expr expr DUP_TOP_TWO BINARY_SUBSCR

        # unary_op (formerly "unary_expr") is the Python AST UnaryOp
        unary_op          ::= expr unary_operator

        unary_operator    ::= UNARY_POSITIVE
        unary_operator    ::= UNARY_NEGATIVE
        unary_operator    ::= UNARY_INVERT

        unary_not         ::= expr UNARY_NOT

        yield             ::= expr YIELD_VALUE
        """

    def p_comprehension_list(self, args):
        """
        lc_body         ::= expr LIST_APPEND
        list_comp       ::= BUILD_LIST_0 list_iter

        list_iter       ::= list_for
        list_iter       ::= list_if
        list_iter       ::= list_if_not
        list_iter       ::= list_if_or_not
        list_iter       ::= lc_body

        set_iter        ::= set_for
        set_iter        ::= list_if
        # set_iter        ::= list_if_and_or
        # set_iter        ::= list_if_chained
        set_iter        ::= list_if_not
        set_iter        ::= set_comp_body

        list_for  ::= expr_or_arg
                      for_iter
                      store list_iter
                      jb_or_c _come_froms

        set_for   ::= expr_or_arg
                      for_iter
                      store set_iter
                      jb_or_c _come_froms

        list_if_not_end ::= pjump_ift _come_froms
        list_if_not ::= expr list_if_not_end list_iter come_from_opt

        list_if     ::= expr pjump_iff list_iter come_from_opt
        list_if     ::= expr jump_if_false_cf   list_iter
        list_if_or_not ::= expr_pjit expr_pjit COME_FROM list_iter

        list_if_end ::= pjump_iff _come_froms
        list_if     ::= expr list_if_end list_iter come_from_opt

        jb_or_c ::= JUMP_LOOP
        jb_or_c ::= CONTINUE


        """

    def p_37conditionals(self, args):
        """
        expr                       ::= if_exp_compare
        bool_op                    ::= and_cond
        bool_op                    ::= and_not_cond
        bool_op                    ::= and POP_JUMP_IF_TRUE expr

        expr_pjif                  ::= expr POP_JUMP_IF_FALSE
        expr_pjit                  ::= expr POP_JUMP_IF_TRUE
        expr_pjitt                 ::= expr pjump_ift
        expr_jifop                 ::= expr JUMP_IF_FALSE_OR_POP
        expr_jitop                 ::= expr JUMP_IF_TRUE_OR_POP
        expr_pjiff                 ::= expr pjump_iff
        expr_pjift                 ::= expr pjump_ift

        if_exp                     ::= expr_pjif expr jump_forward_else expr come_froms

        if_exp_compare             ::= expr expr jf_cfs expr COME_FROM
        if_exp_compare             ::= bool_op expr jf_cfs expr COME_FROM

        if_exp_loop                ::= expr_pjif
                                       expr
                                       POP_JUMP_IF_FALSE_LOOP
                                       JUMP_FORWARD
                                       come_froms
                                       expr

        jf_cfs                     ::= JUMP_FORWARD _come_froms
        list_iter                  ::= list_if37
        list_iter                  ::= list_if37_not
        list_if37                  ::= c_compare_chained37_false list_iter
        list_if37_not              ::= compare_chained37 list_iter

        # A reduction check distinguishes between "and" and "and_not"
        # based on whether the POP_IF_JUMP location matches the location of the
        # POP_JUMP_IF_FALSE.
        and_not                    ::= expr_pjif expr_pjit
        or_and_not                 ::= expr_pjit and_not COME_FROM

        not_and_not                ::= not expr_pjif COME_FROM

        expr                       ::= if_exp_37a
        expr                       ::= if_exp_37b
        if_exp_37a                 ::= and_not expr JUMP_FORWARD come_froms expr COME_FROM
        if_exp_37b                 ::= expr_pjif expr_pjif jump_forward_else expr
        """

    def p_comprehension(self, args):
        """
        # Python3 scanner adds LOAD_LISTCOMP. Python3 does list comprehension like
        # other comprehensions (set, dictionary).

        comp_body      ::= dict_comp_body
        comp_body      ::= gen_comp_body
        # FIXME: decompile-cfg has this. We are missing a LHS rule?
        # comp_body      ::= list_comp_body
        comp_body      ::= set_comp_body

        # Our "continue" heuristic -  in two successive JUMP_LOOPS, the first
        # one may be a continue - sometimes classifies a JUMP_LOOP
        # as a CONTINUE. The two are kind of the same in a comprehension.

        comp_for       ::= expr get_for_iter store comp_iter
                           CONTINUE
                           _come_froms

        comp_for       ::= expr get_for_iter store comp_iter
                           JUMP_LOOP
                           _come_froms

        get_for_iter   ::= GET_ITER _come_froms FOR_ITER

        dict_comp_body ::= expr expr MAP_ADD
        set_comp_body  ::= expr SET_ADD

        # See also common Python p_list_comprehension

        comp_if        ::= expr_pjif comp_iter
        comp_if         ::= expr_pjiff comp_iter
        comp_if         ::= c_compare comp_iter
        comp_if         ::= or_jump_if_false_cf comp_iter
        comp_if         ::= or_jump_if_false_loop_cf comp_iter

        # We need to have a reduction rule to disambiguate
        # these "comp_if_not" and "comp_if". The difference is buried in the
        # sense of the jump in
        #     comp_iter -> comp_if_or -> or_parts_false_loop
        # vs.:
        #    comp_iter -> comp_if_or -> or_parts_true_loop
        #
        # If "true_loop then that goes with "comp_if_not"
        # if "false_loop"  then that goes with comp_if"
        #
        # We might be able to do this in the grammar but it is a bit
        # too pervasive and involved.

        # We have a bunch of these comp_if_<logic expression>
        # because the logic operation bleeds into the
        # "if" of the comprehension. Note thet specific position of
        # POP_JUMP_IF_xxx_LOOP stays the same.
        comp_if_or      ::= or_parts
                            expr POP_JUMP_IF_FALSE_LOOP
                            come_froms
                            comp_iter
        # comp_if_or      ::= or_parts_true_loop
        #                     expr POP_JUMP_IF_FALSE_LOOP
        #                     come_froms
        #                     comp_iter

        # comp_if_or      ::= or_parts_false_loop
        #                     expr POP_JUMP_IF_FALSE_LOOP
        #                     come_froms
        #                     comp_iter

        # Here, the "or" is melded a little into the "comp_if" test
        comp_if_or2     ::= compare compare_chained37_false comp_iter

        comp_if_or_not  ::= or_parts
                            expr POP_JUMP_IF_TRUE_LOOP
                            come_froms
                            comp_iter
        ## FIXME: we add this, per comment above later.
        ## comp_if         ::= expr pjump_ift comp_iter
        comp_if_not     ::= expr pjump_ift comp_iter


        comp_if_not_and ::= expr_pjif
                            expr POP_JUMP_IF_TRUE_LOOP
                            come_froms
                            comp_iter
        comp_if_not_or  ::= expr_pjif
                            expr POP_JUMP_IF_FALSE_LOOP
                            come_from_opt
                            comp_iter

        comp_iter     ::= dict_comp_body
        comp_iter     ::= comp_body
        comp_iter     ::= comp_if
        comp_iter     ::= comp_if_not
        comp_iter     ::= comp_if_not_and
        comp_iter     ::= comp_if_not_or
        comp_iter     ::= comp_if_or
        comp_iter     ::= comp_if_or_not
        comp_iter     ::= comp_if_or2

        or_jump_if_false_cf      ::= or POP_JUMP_IF_FALSE COME_FROM
        or_jump_if_false_loop_cf ::= or_loop POP_JUMP_IF_FALSE_LOOP COME_FROM

        or_loop       ::= or
        or_loop       ::= or_parts_loop expr
        or_parts_loop ::= expr_pjift+

        # Semantic rules require "comp_if" to have index 0 be some
        # sort of "expr" and index 1 to be some sort of "comp_iter"
        c_compare     ::= compare

        expr_or_arg     ::= LOAD_ARG
        expr_or_arg     ::= expr

        ending_return  ::= RETURN_VALUE RETURN_LAST
        ending_return  ::= RETURN_VALUE_LAMBDA LAMBDA_MARKER

        for_iter       ::= _come_froms FOR_ITER
        dict_comp_func ::= BUILD_MAP_0 LOAD_ARG for_iter store
                           comp_iter JUMP_LOOP _come_froms
                           ending_return

        set_comp_func   ::= BUILD_SET_0
                            expr_or_arg
                            for_iter store comp_iter
                            JUMP_LOOP
                            _come_froms
                            ending_return

        set_comp_func   ::= BUILD_SET_0
                            expr_or_arg
                            for_iter store comp_iter
                            COME_FROM
                            JUMP_LOOP
                            _come_froms
                            ending_return

        await_expr       ::= expr GET_AWAITABLE LOAD_CONST YIELD_FROM
        set_comp_func    ::= BUILD_SET_0
                             expr_or_arg
                             for_iter store await_expr
                             SET_ADD
                             JUMP_LOOP
                             _come_froms
                             ending_return
        """

    def p_expr3(self, args):
        """
        expr               ::= if_exp_not
        if_exp_not         ::= expr POP_JUMP_IF_TRUE expr jump_forward_else expr COME_FROM

        # a JUMP_FORWARD to another JUMP_FORWARD can get turned into
        # a JUMP_ABSOLUTE with no COME_FROM
        if_exp             ::= expr_pjif expr jump_forward_else expr

        # if_exp_true are are IfExp which always evaluate true, e.g.:
        #      x = a if 1 else b
        # There is dead or non-optional remnants of the condition code though,
        # and we use that to match on to reconstruct the source more accurately
        expr           ::= if_exp_true
        if_exp_true    ::= expr JUMP_FORWARD expr COME_FROM

        """

    def p_set_comp(self, args):
        """
        comp_iter     ::= comp_for
        gen_comp_body ::= expr YIELD_VALUE POP_TOP
        set_comp      ::= BUILD_SET_0 set_iter
        """

    def p_store(self, args):
        """
        # Note. The below is right-recursive:
        designList ::= store store
        designList ::= store DUP_TOP designList

        ## Can we replace with left-recursive, and redo with:
        ##
        ##   designList  ::= designLists store store
        ##   designLists ::= designLists store DUP_TOP
        ##   designLists ::=
        ## Will need to redo semantic actiion

        store           ::= STORE_FAST
        store           ::= STORE_NAME
        store           ::= STORE_GLOBAL
        store           ::= STORE_DEREF
        store           ::= expr STORE_ATTR
        store           ::= store_subscript
        store_subscript ::= expr expr STORE_SUBSCR
        """


if __name__ == "__main__":
    # Check grammar
    from decompyle3.parsers.dump import dump_and_check

    p = Python37LambdaParser()
    modified_tokens = set(
        """JUMP_LOOP CONTINUE RETURN_END_IF_LAMBDA COME_FROM
           LOAD_GENEXPR LOAD_ASSERT LOAD_SETCOMP LOAD_DICTCOMP LOAD_CLASSNAME
           LAMBDA_MARKER RETURN_VALUE_LAMBDA
        """.split()
    )

    dump_and_check(p, (3, 7), modified_tokens)
