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
Python 3.7 lambda grammar for the spark Earley-algorithm parser.
"""

from decompyle3.parsers.main import nop_func
from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from decompyle3.parsers.p37.base import Python37BaseParser
from decompyle3.scanners.tok import Token


class Python37LambdaParser(Python37BaseParser):
    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG, compile_mode="lambda"):
        super(Python37LambdaParser, self).__init__(debug_parser, compile_mode=compile_mode)
        self.customized = {}
    ###################################################
    #  Python 3.7 grammar rules for lambda expressions
    ###################################################
    pass

    def p_lambda(self, args):
        """
        lambda_start       ::= return_lambda LAMBDA_MARKER
        return_lambda      ::= expr RETURN_VALUE_LAMBDA
        return_lambda      ::= if_exp_lambda
        return_lambda      ::= if_exp_lambda2
        return_lambda      ::= if_exp_not_lambda
        return_lambda      ::= if_exp_dead_code

        return_if_lambda   ::= RETURN_END_IF_LAMBDA COME_FROM
        return_if_lambda   ::= RETURN_END_IF_LAMBDA

        if_exp_lambda      ::= expr_pjif expr return_if_lambda
                               return_lambda LAMBDA_MARKER
        if_exp_lambda2     ::= and_parts return_lambda come_froms
                               return_lambda opt_lambda_marker
        if_exp_not_lambda  ::= expr POP_JUMP_IF_TRUE expr return_if_lambda
                               return_lambda LAMBDA_MARKER
        if_exp_dead_code   ::= return_lambda return_lambda
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

        not        ::= expr_pjit

        and_parts  ::= expr_pjif+

        # Note: "and" like "nor" might not have a trailing "come_from".
        #       "nand" and "or", in contrast, *must* have at least one "come_from".
        not_or     ::= and_parts expr_pjif _come_froms
        and_cond   ::= and_parts expr_pjif _come_froms

        and        ::= and_parts expr
        and        ::= not expr

        nand       ::= and_parts expr_pjit  come_froms
        c_nand     ::= and_parts expr_pjitt come_froms

        or_parts  ::= expr_pjit+

        # Note: "nor" like "and" might not have a trailing "come_from".
        #       "nand" and "or_cond", in contrast, *must* have at least one "come_from".
        or_cond     ::= or_parts expr_pjif come_froms
        or_cond1    ::= and POP_JUMP_IF_TRUE come_froms expr_pjif come_from_opt
        nor_cond    ::= or_parts expr_pjit

        # When we alternating and/or's such as:
        #    a and (b or c) and d
        # instead of POP_JUMP_IF_TRUE, JUMP_IF_FALSE_OR_POP can be used
        # The semantic rules for "and" require expr-like things in positions 0 and 1,
        # thus the use of expr_jifop_cfs below.

        expr_jifop_cfs ::= expr JUMP_IF_FALSE_OR_POP _come_froms
        and            ::= expr_jifop_cfs expr _come_froms

        ## A COME_FROM is dropped off because of JUMP-to-JUMP optimization
        # and       ::= expr_pjif expr

        ## Note that "POP_JUMP_IF_FALSE" is what we check on in the "and" reduce rule.
        # and       ::= expr_pjif expr COME_FROM

        jump_if_false_cf ::= POP_JUMP_IF_FALSE COME_FROM

        and_or_cond ::= and_parts expr POP_JUMP_IF_TRUE come_froms expr_pjif _come_froms

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


        or        ::= expr_pjit expr COME_FROM
        or_expr   ::= expr JUMP_IF_TRUE expr COME_FROM

        jitop_come_from_expr ::= JUMP_IF_TRUE_OR_POP _come_froms expr
        or                   ::= and jitop_come_from_expr COME_FROM
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
        jump               ::= JUMP_BACK
        jump_or_break      ::= jump
        jump_or_break      ::= BREAK_LOOP

        # These are used to keep parse tree indices the same
        # in "if"/"else" like rules.
        jump_forward_else  ::= JUMP_FORWARD _come_froms
        jump_forward_else  ::= come_froms jump COME_FROM

        pjump_ift          ::= POP_JUMP_IF_TRUE
        pjump_ift          ::= POP_JUMP_IF_TRUE_BACK

        pjump_iff          ::= POP_JUMP_IF_FALSE
        pjump_iff          ::= POP_JUMP_IF_FALSE_BACK

        # pjump              ::= pjump_iff
        # pjump              ::= pjump_ift
        """

    def p_37chained(self, args):
        """
        # A compare_chained is two comparisions like x <= y <= z
        compare_chained     ::= expr compare_chained1 ROT_TWO POP_TOP _come_froms
        compare_chained     ::= compare_chained37
        compare_chained     ::= compare_chained37_false

        c_compare_chained   ::= c_compare_chained37_false

        compare_chained37   ::= expr chained_parts
        compare_chained37   ::= expr compare_chained1a_37
        compare_chained37   ::= expr compare_chained1c_37
        c_compare_chained37   ::= expr c_compare_chained1a_37
        # c_compare_chained37   ::= expr c_compare_chained1c_37

        compare_chained37_false   ::= expr compare_chained1_false_37
        compare_chained37_false   ::= expr compare_chained1b_false_37
        compare_chained37_false   ::= expr compare_chained2_false_37

        c_compare_chained37_false ::= expr c_compare_chained2_false_37
        c_compare_chained37_false ::= expr c_compare_chained1b_false_37
        c_compare_chained37_false ::= compare_chained37_false

        compare_chained1           ::= expr DUP_TOP ROT_THREE COMPARE_OP JUMP_IF_FALSE_OR_POP
                                       compare_chained1 COME_FROM
        compare_chained1           ::= expr DUP_TOP ROT_THREE COMPARE_OP JUMP_IF_FALSE_OR_POP
                                      compare_chained2 COME_FROM

        chained_parts              ::= chained_part+
        chained_part               ::= expr DUP_TOP ROT_THREE COMPARE_OP come_from_opt POP_JUMP_IF_FALSE

        # c_chained_parts            ::= c_chained_part+
        # c_chained_part             ::= expr DUP_TOP ROT_THREE COMPARE_OP come_from_opt POP_JUMP_IF_FALSE_BACK
        # c_chained_parts            ::= chained_parts


        compare_chained1a_37       ::= chained_parts
                                       compare_chained2a_37 COME_FROM
                                       POP_TOP come_from_opt
        c_compare_chained1a_37     ::= chained_parts
                                       c_compare_chained2a_37 COME_FROM
                                       POP_TOP come_from_opt

        compare_chained1b_false_37 ::= chained_parts
                                       compare_chained2b_false_37
                                       POP_TOP jump _come_froms

        c_compare_chained1b_false_37 ::= chained_parts
                                         c_compare_chained2b_false_37 POP_TOP jump _come_froms
        c_compare_chained1b_false_37 ::= chained_parts
                                         compare_chained2b_false_37 POP_TOP jump _come_froms

        compare_chained1c_37       ::= chained_parts
                                       compare_chained2a_37 POP_TOP

        compare_chained1_false_37  ::= chained_parts
                                       compare_chained2c_37 POP_TOP JUMP_FORWARD come_from_opt
        compare_chained1_false_37  ::= chained_parts
                                       compare_chained2b_false_37 POP_TOP jump COME_FROM

        compare_chained2           ::= expr COMPARE_OP JUMP_FORWARD
        compare_chained2           ::= expr COMPARE_OP JUMP_FORWARD
        compare_chained2           ::= expr COMPARE_OP RETURN_VALUE
        compare_chained2           ::= expr COMPARE_OP RETURN_VALUE_LAMBDA

        compare_chained2_false_37  ::= chained_parts
                                      compare_chained2a_false_37 POP_TOP JUMP_BACK COME_FROM
        c_compare_chained2_false_37  ::= chained_parts
                                         c_compare_chained2a_false_37 POP_TOP JUMP_BACK COME_FROM

        compare_chained2a_37       ::= expr COMPARE_OP come_from_opt POP_JUMP_IF_TRUE JUMP_FORWARD
        c_compare_chained2a_37     ::= expr COMPARE_OP come_from_opt POP_JUMP_IF_TRUE_BACK JUMP_FORWARD


        compare_chained2a_37       ::= expr COMPARE_OP come_from_opt POP_JUMP_IF_TRUE JUMP_BACK
        compare_chained2a_false_37 ::= expr COMPARE_OP come_from_opt POP_JUMP_IF_FALSE jf_cfs


        compare_chained2b_false_37   ::= expr COMPARE_OP come_from_opt POP_JUMP_IF_FALSE
                                         jump_or_break COME_FROM
        c_compare_chained2b_false_37 ::= expr COMPARE_OP come_from_opt POP_JUMP_IF_FALSE_BACK
                                         jump_or_break COME_FROM
        c_compare_chained2a_false_37 ::= expr COMPARE_OP come_from_opt POP_JUMP_IF_FALSE_BACK
                                         jf_cfs
        c_compare_chained2a_false_37 ::= expr COMPARE_OP come_from_opt POP_JUMP_IF_FALSE_BACK
        c_compare_chained2b_false_37 ::= expr COMPARE_OP come_from_opt JUMP_FORWARD COME_FROM


        compare_chained2c_37       ::= chained_parts compare_chained2a_false_37
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
        expr ::= bin_op
        expr ::= call
        expr ::= compare
        expr ::= or
        expr ::= or_expr
        expr ::= subscript
        expr ::= subscript2
        expr ::= unary_not
        expr ::= unary_op
        expr ::= not
        expr ::= yield
        expr ::= attribute37

        # Python 3.3+ adds yield from.
        expr          ::= yield_from
        yield_from    ::= expr GET_YIELD_FROM_ITER LOAD_CONST YIELD_FROM

        attribute37       ::= expr LOAD_METHOD

        # bin_op (formerly "binary_expr") is the Python AST BinOp
        bin_op            ::= expr expr binary_operator

        binary_operator   ::= BINARY_ADD
        binary_operator   ::= BINARY_MULTIPLY
        binary_operator   ::= BINARY_AND
        binary_operator   ::= BINARY_OR
        binary_operator   ::= BINARY_XOR
        binary_operator   ::= BINARY_SUBTRACT
        binary_operator   ::= BINARY_TRUE_DIVIDE
        binary_operator   ::= BINARY_FLOOR_DIVIDE
        binary_operator   ::= BINARY_MODULO
        binary_operator   ::= BINARY_LSHIFT
        binary_operator   ::= BINARY_RSHIFT
        binary_operator   ::= BINARY_POWER

        # unary_op (formerly "unary_expr") is the Python AST UnaryOp
        unary_op          ::= expr unary_operator

        unary_operator    ::= UNARY_POSITIVE
        unary_operator    ::= UNARY_NEGATIVE
        unary_operator    ::= UNARY_INVERT

        unary_not         ::= expr UNARY_NOT

        subscript         ::= expr expr BINARY_SUBSCR
        subscript2        ::= expr expr DUP_TOP_TWO BINARY_SUBSCR

        yield             ::= expr YIELD_VALUE

        expr              ::= if_exp

        compare           ::= compare_chained
        compare           ::= compare_single
        compare_single    ::= expr expr COMPARE_OP
        c_compare         ::= c_compare_chained


        # FIXME: the below is to work around test_grammar expecting a "call" to be
        # on the LHS because it is also somewhere on in a rule.
        call           ::= expr CALL_METHOD_0
        """

    def p_list_comprehension(self, args):
        """
        expr ::= list_comp

        list_iter ::= list_for
        list_iter ::= list_if
        list_iter ::= list_if_not
        list_iter ::= list_if_or_not
        list_iter ::= lc_body

        lc_body   ::= expr LIST_APPEND
        list_for  ::= expr for_iter store list_iter jb_or_c _come_froms
        list_comp ::= BUILD_LIST_0 list_iter

        list_if     ::= expr pjump_iff list_iter come_from_opt
        list_if_not ::= expr pjump_ift list_iter come_from_opt
        list_if     ::= expr jump_if_false_cf   list_iter
        list_if_or_not ::= expr_pjit expr_pjit COME_FROM list_iter

        jb_or_c ::= JUMP_BACK
        jb_or_c ::= CONTINUE


        """

    def p_37conditionals(self, args):
        """
        expr                       ::= if_exp37
        bool_op                    ::= and_cond
        bool_op                    ::= and POP_JUMP_IF_TRUE expr

        expr_pjif                  ::= expr POP_JUMP_IF_FALSE
        expr_pjit                  ::= expr POP_JUMP_IF_TRUE
        expr_pjitt                 ::= expr pjump_ift
        expr_jitop                 ::= expr JUMP_IF_TRUE_OR_POP
        expr_pjiff                 ::= expr pjump_iff
        expr_pjift                 ::= expr pjump_ift

        if_exp                     ::= expr_pjif expr jump_forward_else expr come_froms

        if_exp37                   ::= expr expr    jf_cfs expr COME_FROM
        if_exp37                   ::= bool_op expr jf_cfs expr COME_FROM
        jf_cfs                     ::= JUMP_FORWARD _come_froms
        list_iter                  ::= list_if37
        list_iter                  ::= list_if37_not
        list_if37                  ::= c_compare_chained37_false list_iter
        list_if37_not              ::= compare_chained37 list_iter

        # A reduction check distinguishes between "and" and "and_not"
        # based on whether the POP_IF_JUMP location matches the location of the
        # POP_JUMP_IF_FALSE.
        and_not                    ::= expr_pjif expr POP_JUMP_IF_TRUE
        or_and_not                 ::= expr POP_JUMP_IF_TRUE and_not COME_FROM

        expr                       ::= if_exp_37a
        expr                       ::= if_exp_37b
        if_exp_37a                 ::= and_not expr JUMP_FORWARD come_froms expr COME_FROM
        if_exp_37b                 ::= expr_pjif expr_pjif jump_forward_else expr
        """


    def p_comprehension3(self, args):
        """
        # Python3 scanner adds LOAD_LISTCOMP. Python3 does list comprehension like
        # other comprehensions (set, dictionary).

        # Our "continue" heuristic -  in two successive JUMP_BACKS, the first
        # one may be a continue - sometimes classifies a JUMP_BACK
        # as a CONTINUE. The two are kind of the same in a comprehension.

        comp_for       ::= expr get_for_iter store comp_iter CONTINUE _come_froms
        comp_for       ::= expr get_for_iter store comp_iter JUMP_BACK _come_froms
        get_for_iter   ::= GET_ITER _come_froms FOR_ITER

        comp_body      ::= dict_comp_body
        comp_body      ::= set_comp_body
        dict_comp_body ::= expr expr MAP_ADD
        set_comp_body  ::= expr SET_ADD

        # See also common Python p_list_comprehension
        """

    def p_dict_comp3(self, args):
        """"
        or_jump_if_false_cf    ::= or POP_JUMP_IF_FALSE COME_FROM
        c_or_jump_if_false_cf  ::= c_or POP_JUMP_IF_FALSE_BACK COME_FROM

        c_or       ::= or
        c_or       ::= c_or_parts expr
        c_or_parts ::= expr_pjift+

        # Semantic rules require "comp_if" to have index 0 be some
        # sort of "expr" and index 1 to be some sort of "comp_iter"
        c_compare     ::= compare

        comp_if       ::= expr_pjif comp_iter
        comp_if       ::= expr_pjiff comp_iter
        comp_if       ::= c_compare comp_iter
        comp_if       ::= or_jump_if_false_cf comp_iter
        comp_if       ::= c_or_jump_if_false_cf comp_iter
        comp_if_not   ::= expr pjump_ift comp_iter

        comp_iter     ::= comp_body
        comp_iter     ::= comp_if
        comp_iter     ::= comp_if_not
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
        comp_body     ::= gen_comp_body
        gen_comp_body ::= expr YIELD_VALUE POP_TOP
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

    def customize_grammar_rules(self, tokens, customize):
        super(Python37LambdaParser, self).customize_grammar_rules(tokens, customize)
        self.check_reduce["call_kw"] = "AST"

        for i, token in enumerate(tokens):
            opname = token.kind

            if opname == "LOAD_ASSERT":
                if "PyPy" in customize:
                    rules_str = """
                    stmt ::= JUMP_IF_NOT_DEBUG stmts COME_FROM
                    """
                    self.add_unique_doc_rules(rules_str, customize)
            elif opname == "FORMAT_VALUE":
                rules_str = """
                    expr              ::= formatted_value1
                    formatted_value1  ::= expr FORMAT_VALUE
                """
                self.add_unique_doc_rules(rules_str, customize)
            elif opname == "FORMAT_VALUE_ATTR":
                rules_str = """
                expr              ::= formatted_value2
                formatted_value2  ::= expr expr FORMAT_VALUE_ATTR
                """
                self.add_unique_doc_rules(rules_str, customize)
            elif opname == "MAKE_FUNCTION_8":
                if "LOAD_DICTCOMP" in self.seen_ops:
                    # Is there something general going on here?
                    rule = """
                       dict_comp ::= load_closure LOAD_DICTCOMP LOAD_STR
                                     MAKE_FUNCTION_8 expr
                                     GET_ITER CALL_FUNCTION_1
                       """
                    self.addRule(rule, nop_func)
                elif "LOAD_SETCOMP" in self.seen_ops:
                    rule = """
                       set_comp ::= load_closure LOAD_SETCOMP LOAD_STR
                                    MAKE_FUNCTION_8 expr
                                    GET_ITER CALL_FUNCTION_1
                       """
                    self.addRule(rule, nop_func)

            elif opname == "BEFORE_ASYNC_WITH":
                rules_str = """
                  stmt               ::= async_with_stmt SETUP_ASYNC_WITH
                  async_with_pre     ::= BEFORE_ASYNC_WITH GET_AWAITABLE LOAD_CONST YIELD_FROM SETUP_ASYNC_WITH
                  async_with_post    ::= COME_FROM_ASYNC_WITH
                                         WITH_CLEANUP_START GET_AWAITABLE LOAD_CONST YIELD_FROM
                                         WITH_CLEANUP_FINISH END_FINALLY

                  stmt               ::= async_with_as_stmt
                  async_with_as_stmt ::= expr
                                         async_with_pre
                                         store
                                         suite_stmts_opt
                                         POP_BLOCK LOAD_CONST
                                         async_with_post

                 async_with_stmt     ::= expr
                                         async_with_pre
                                         POP_TOP
                                         suite_stmts_opt
                                         POP_BLOCK LOAD_CONST
                                         async_with_post
                 async_with_stmt     ::= expr
                                         async_with_pre
                                         POP_TOP
                                         suite_stmts_opt
                                         async_with_post
                """
                self.addRule(rules_str, nop_func)

            elif opname.startswith("BUILD_STRING"):
                v = token.attr
                rules_str = """
                    expr                 ::= joined_str
                    joined_str           ::= %sBUILD_STRING_%d
                """ % (
                    "expr " * v,
                    v,
                )
                self.add_unique_doc_rules(rules_str, customize)
                if "FORMAT_VALUE_ATTR" in self.seen_ops:
                    rules_str = """
                      formatted_value_attr ::= expr expr FORMAT_VALUE_ATTR expr BUILD_STRING
                      expr                 ::= formatted_value_attr
                    """
                    self.add_unique_doc_rules(rules_str, customize)
            elif opname.startswith("BUILD_MAP_UNPACK_WITH_CALL"):
                v = token.attr
                rule = "build_map_unpack_with_call ::= %s%s" % ("expr " * v, opname)
                self.addRule(rule, nop_func)
            elif opname.startswith("BUILD_TUPLE_UNPACK_WITH_CALL"):
                v = token.attr
                rule = (
                    "build_tuple_unpack_with_call ::= "
                    + "expr1024 " * int(v // 1024)
                    + "expr32 " * int((v // 32) % 32)
                    + "expr " * (v % 32)
                    + opname
                )
                self.addRule(rule, nop_func)
                rule = "starred ::= %s %s" % ("expr " * v, opname)
                self.addRule(rule, nop_func)
            elif opname == "SETUP_WITH":
                rules_str = """
                with       ::= expr SETUP_WITH POP_TOP suite_stmts_opt COME_FROM_WITH
                               WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY

                # Removes POP_BLOCK LOAD_CONST from 3.6-
                withasstmt ::= expr SETUP_WITH store suite_stmts_opt COME_FROM_WITH
                               WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY
                """
                if self.version < 3.8:
                    rules_str += """
                    with       ::= expr SETUP_WITH POP_TOP suite_stmts_opt POP_BLOCK
                                   LOAD_CONST
                                   WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY
                    """
                else:
                    rules_str += """
                    with        ::= expr SETUP_WITH POP_TOP suite_stmts_opt POP_BLOCK
                                   BEGIN_FINALLY COME_FROM_WITH
                                   WITH_CLEANUP_START WITH_CLEANUP_FINISH
                                   END_FINALLY
                    """
                self.addRule(rules_str, nop_func)
                pass
            pass

    def custom_classfunc_rule(self, opname, token, customize, next_token):

        args_pos, args_kw = self.get_pos_kw(token)

        # Additional exprs for * and ** args:
        #  0 if neither
        #  1 for CALL_FUNCTION_VAR or CALL_FUNCTION_KW
        #  2 for * and ** args (CALL_FUNCTION_VAR_KW).
        # Yes, this computation based on instruction name is a little bit hoaky.
        nak = (len(opname) - len("CALL_FUNCTION")) // 3
        uniq_param = args_kw + args_pos

        if frozenset(("GET_AWAITABLE", "YIELD_FROM")).issubset(self.seen_ops):
            rule = (
                "async_call ::= expr "
                + ("expr " * args_pos)
                + ("kwarg " * args_kw)
                + "expr " * nak
                + token.kind
                + " GET_AWAITABLE LOAD_CONST YIELD_FROM"
            )
            self.add_unique_rule(rule, token.kind, uniq_param, customize)
            self.add_unique_rule(
                "expr ::= async_call", token.kind, uniq_param, customize
            )

        if opname.startswith("CALL_FUNCTION_KW"):
            self.addRule("expr ::= call_kw36", nop_func)
            values = "expr " * token.attr
            rule = "call_kw36 ::= expr {values} LOAD_CONST {opname}".format(**locals())
            self.add_unique_rule(rule, token.kind, token.attr, customize)
        elif opname == "CALL_FUNCTION_EX_KW":
            # Note: this doesn't exist in 3.7 and later
            self.addRule(
                """expr        ::= call_ex_kw4
                            call_ex_kw4 ::= expr
                                            expr
                                            expr
                                            CALL_FUNCTION_EX_KW
                         """,
                nop_func,
            )
            if "BUILD_MAP_UNPACK_WITH_CALL" in self.seen_op_basenames:
                self.addRule(
                    """expr        ::= call_ex_kw
                                call_ex_kw  ::= expr expr build_map_unpack_with_call
                                                CALL_FUNCTION_EX_KW
                             """,
                    nop_func,
                )
            if "BUILD_TUPLE_UNPACK_WITH_CALL" in self.seen_op_basenames:
                # FIXME: should this be parameterized by EX value?
                self.addRule(
                    """expr        ::= call_ex_kw3
                                call_ex_kw3 ::= expr
                                                build_tuple_unpack_with_call
                                                expr
                                                CALL_FUNCTION_EX_KW
                             """,
                    nop_func,
                )
                if "BUILD_MAP_UNPACK_WITH_CALL" in self.seen_op_basenames:
                    # FIXME: should this be parameterized by EX value?
                    self.addRule(
                        """expr        ::= call_ex_kw2
                                    call_ex_kw2 ::= expr
                                                    build_tuple_unpack_with_call
                                                    build_map_unpack_with_call
                                                    CALL_FUNCTION_EX_KW
                             """,
                        nop_func,
                    )

        elif opname == "CALL_FUNCTION_EX":
            self.addRule(
                """
                         expr        ::= call_ex
                         starred     ::= expr
                         call_ex     ::= expr starred CALL_FUNCTION_EX
                         """,
                nop_func,
            )
            if "BUILD_MAP_UNPACK_WITH_CALL" in self.seen_ops:
                self.addRule(
                    """
                        expr        ::= call_ex_kw
                        call_ex_kw  ::= expr expr
                                        build_map_unpack_with_call CALL_FUNCTION_EX
                        """,
                    nop_func,
                )
            if "BUILD_TUPLE_UNPACK_WITH_CALL" in self.seen_ops:
                self.addRule(
                    """
                        expr        ::= call_ex_kw3
                        call_ex_kw3 ::= expr
                                        build_tuple_unpack_with_call
                                        %s
                                        CALL_FUNCTION_EX
                        """
                    % "expr "
                    * token.attr,
                    nop_func,
                )
                pass

            # FIXME: Is this right?
            self.addRule(
                """
                        expr        ::= call_ex_kw4
                        call_ex_kw4 ::= expr
                                        expr
                                        expr
                                        CALL_FUNCTION_EX
                        """,
                nop_func,
            )
            pass
        else:
            super(Python37LambdaParser, self).custom_classfunc_rule(
                opname, token, customize, next_token
            )

    def reduce_is_invalid(self, rule, ast, tokens, first, last):
        invalid = super(Python37LambdaParser, self).reduce_is_invalid(
            rule, ast, tokens, first, last
        )
        if invalid:
            return invalid
        if rule[0] == "call_kw":
            # Make sure we don't derive call_kw
            nt = ast[0]
            while not isinstance(nt, Token):
                if nt[0] == "call_kw":
                    return True
                nt = nt[0]
                pass
            pass
        return False

if __name__ == "__main__":
    # Check grammar
    from decompyle3.parsers.dump import dump_and_check
    p = Python37LambdaParser()
    modified_tokens = set(
        """JUMP_BACK CONTINUE RETURN_END_IF_LAMBDA COME_FROM
           LOAD_GENEXPR LOAD_ASSERT LOAD_SETCOMP LOAD_DICTCOMP LOAD_CLASSNAME
           LAMBDA_MARKER RETURN_VALUE_LAMBDA
        """.split()
        )

    dump_and_check(p, 3.7, modified_tokens)
