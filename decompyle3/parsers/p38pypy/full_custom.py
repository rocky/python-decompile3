#  Copyright (c) 2021-2024 Rocky Bernstein
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

# from decompyle3.parsers.reduce_check.import_from37 import import_from37_ok
from decompyle3.parsers.p37.base import Python37BaseParser
from decompyle3.parsers.p38.lambda_custom import Python38LambdaCustom
from decompyle3.parsers.parse_heads import PythonBaseParser, nop_func
from decompyle3.parsers.reduce_check import (  # joined_str_check,
    break_invalid,
    for38_invalid,
    forelse38_invalid,
    if_not_stmtc_invalid,
    pop_return_check,
    whilestmt38_check,
    whileTruestmt38_check,
)

# from decompyle3.parsers.reduce_check.ifelsestmt_check import ifelsestmt_ok
from decompyle3.parsers.reduce_check.ifstmt import ifstmt
from decompyle3.parsers.reduce_check.or_cond_check import or_cond_check_invalid


class Python38PyPyFullCustom(Python38LambdaCustom, PythonBaseParser):
    def add_make_function_rule(self, rule, opname, attr, customize):
        """Python 3.3 added an additional LOAD_STR before MAKE_FUNCTION and
        this has an effect on many rules.
        """
        new_rule = rule % "LOAD_STR "
        self.add_unique_rule(new_rule, opname, attr, customize)

    @staticmethod
    def call_fn_name(token):
        """Customize CALL_FUNCTION to add the number of positional arguments"""
        if token.attr is not None:
            return f"{token.kind}_{token.attr}"
        else:
            return f"{token.kind}_0"

    def remove_rules_38(self):
        self.remove_rules(
            """
           stmt               ::= async_for_stmt37
           stmt               ::= for
           stmt               ::= forelsestmt
           stmt               ::= try_except36
           stmt               ::= async_forelse_stmt

           # There is no SETUP_LOOP
           setup_loop         ::= SETUP_LOOP _come_froms
           forelselaststmt    ::= SETUP_LOOP expr get_for_iter store
                                  for_block POP_BLOCK else_suitec _come_froms

           forelsestmt        ::= SETUP_LOOP expr get_for_iter store
           whileTruestmt      ::= SETUP_LOOP c_stmts_opt JUMP_LOOP COME_FROM_LOOP
                                  for_block POP_BLOCK else_suite _come_froms

           # async_for_stmt     ::= setup_loop expr
           #                        GET_AITER
           #                        SETUP_EXCEPT GET_ANEXT LOAD_CONST
           #                        YIELD_FROM
           #                        store
           #                        POP_BLOCK JUMP_FORWARD bb_end_start DUP_TOP
           #                        LOAD_GLOBAL COMPARE_OP POP_JUMP_IF_TRUE
           #                        END_FINALLY bb_end_start
           #                        for_block
           #                        COME_FROM
           #                        POP_TOP POP_TOP POP_TOP POP_EXCEPT POP_TOP POP_BLOCK
           #                        COME_FROM_LOOP

           # async_for_stmt37   ::= setup_loop expr
           #                        GET_AITER
           #                        SETUP_EXCEPT GET_ANEXT
           #                        LOAD_CONST YIELD_FROM
           #                        store
           #                        POP_BLOCK JUMP_LOOP COME_FROM_EXCEPT DUP_TOP
           #                        LOAD_GLOBAL COMPARE_OP POP_JUMP_IF_TRUE
           #                        END_FINALLY for_block COME_FROM
           #                        POP_TOP POP_TOP POP_TOP POP_EXCEPT
           #                        POP_TOP POP_BLOCK
           #                        COME_FROM_LOOP

           # async_forelse_stmt ::= setup_loop expr
           #                        GET_AITER
           #                        SETUP_EXCEPT GET_ANEXT LOAD_CONST
           #                        YIELD_FROM
           #                        store
           #                        POP_BLOCK JUMP_FORWARD COME_FROM_EXCEPT DUP_TOP
           #                        LOAD_GLOBAL COMPARE_OP POP_JUMP_IF_TRUE
           #                        END_FINALLY COME_FROM
           #                        for_block
           #                        COME_FROM
           #                        POP_TOP POP_TOP POP_TOP POP_EXCEPT POP_TOP POP_BLOCK
           #                        else_suite COME_FROM_LOOP

           for                ::= setup_loop expr get_for_iter store for_block POP_BLOCK
           for                ::= setup_loop expr get_for_iter store for_block POP_BLOCK NOP

           for_block          ::= c_stmts_opt COME_FROM_LOOP JUMP_LOOP
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

    # def custom_classfunc_rule(self, opname, token, customize, next_token):
    #     """
    #     call ::= expr {expr}^n CALL_FUNCTION_n
    #     call ::= expr {expr}^n CALL_FUNCTION_VAR_n
    #     call ::= expr {expr}^n CALL_FUNCTION_VAR_KW_n
    #     call ::= expr {expr}^n CALL_FUNCTION_KW_n

    #     classdefdeco2 ::= LOAD_BUILD_CLASS mkfunc {expr}^n-1 CALL_FUNCTION_n
    #     """
    #     args_pos, args_kw = self.get_pos_kw(token)

    #     # Additional exprs for * and ** args:
    #     #  0 if neither
    #     #  1 for CALL_FUNCTION_VAR or CALL_FUNCTION_KW
    #     #  2 for * and ** args (CALL_FUNCTION_VAR_KW).
    #     # Yes, this computation based on instruction name is a little bit hoaky.
    #     nak = (len(opname) - len("CALL_FUNCTION")) // 3
    #     uniq_param = args_kw + args_pos
    #     if frozenset(("GET_AWAITABLE", "YIELD_FROM")).issubset(self.seen_ops):
    #         rule = (
    #             "async_call ::= expr "
    #             + ("expr " * args_pos)
    #             + ("kwarg " * args_kw)
    #             + "expr " * nak
    #             + token.kind
    #             + " GET_AWAITABLE LOAD_CONST YIELD_FROM"
    #         )
    #         self.add_unique_rule(rule, token.kind, uniq_param, customize)
    #         self.add_unique_rule(
    #             "expr ::= async_call", token.kind, uniq_param, customize
    #         )

    #     if opname.startswith("CALL_FUNCTION_VAR"):
    #         token.kind = self.call_fn_name(token)
    #         if opname.endswith("KW"):
    #             kw = "expr "
    #         else:
    #             kw = ""
    #         rule = (
    #             "call ::= expr expr "
    #             + ("expr " * args_pos)
    #             + ("kwarg " * args_kw)
    #             + kw
    #             + token.kind
    #         )

    #         # Note: semantic actions make use of the fact of whether "args_pos"
    #         # zero or not in creating a template rule.
    #         self.add_unique_rule(rule, token.kind, args_pos, customize)
    #     else:
    #         token.kind = self.call_fn_name(token)
    #         uniq_param = args_kw + args_pos

    #         # Note: 3.5+ have subclassed this method; so we don't handle
    #         # 'CALL_FUNCTION_VAR' or 'CALL_FUNCTION_EX' here.
    #         rule = (
    #             "call ::= expr "
    #             + ("expr " * args_pos)
    #             + ("kwarg " * args_kw)
    #             + "expr " * nak
    #             + token.kind
    #         )

    #         self.add_unique_rule(rule, token.kind, uniq_param, customize)

    #         if "LOAD_BUILD_CLASS" in self.seen_ops:
    #             if (
    #                 next_token == "CALL_FUNCTION"
    #                 and next_token.attr == 1
    #                 and args_pos > 1
    #             ):
    #                 rule = "classdefdeco2 ::= LOAD_BUILD_CLASS mkfunc %s%s_%d" % (
    #                     ("expr " * (args_pos - 1)),
    #                     opname,
    #                     args_pos,
    #                 )
    #                 self.add_unique_rule(rule, token.kind, uniq_param, customize)

    def customize_grammar_rules_full38(self, tokens, customize):

        self.customize_grammar_rules_lambda38(tokens, customize)
        self.customize_reduce_checks_full38(tokens, customize)
        self.remove_rules_38()

        # include instructions that don't need customization,
        # but we'll do a finer check after the rough breakout.
        customize_instruction_basenames = frozenset(
            (
                "BEFORE",
                "BUILD",
                "CALL",
                "CONTINUE",
                "DELETE",
                "FORMAT",
                "GET",
                "JUMP",
                "LOAD",
                "LOOKUP",
                "MAKE",
                "RETURN",
                "RAISE",
                "SETUP",
                "UNPACK",
                "WITH",
            )
        )

        # Opcode names in the custom_ops_processed set have rules that get added
        # unconditionally and the rules are constant. So they need to be done
        # only once and if we see the opcode a second we don't have to consider
        # adding more rules.
        #
        custom_ops_processed = set()

        # A set of instruction operation names that exist in the token stream.
        # We use this to customize the grammar that we create.
        # 2.6-compatible set comprehensions

        # The initial initialization is done in lambea_expr.py
        self.seen_ops = frozenset([t.kind for t in tokens])
        self.seen_op_basenames = frozenset(
            [opname[: opname.rfind("_")] for opname in self.seen_ops]
        )

        # Loop over instructions adding custom grammar rules based on
        # a specific instruction seen.

        if "PyPy" in customize:
            self.addRule(
                """
              stmt ::= assign3_pypy
              stmt ::= assign2_pypy
              assign3_pypy       ::= expr expr expr store store store
              assign2_pypy       ::= expr expr store store
              """,
                nop_func,
            )

        for i, token in enumerate(tokens):
            opname = token.kind

            # Do a quick breakout before testing potentially
            # each of the dozen or so instruction in if elif.
            if (
                opname[: opname.find("_")] not in customize_instruction_basenames
                or opname in custom_ops_processed
            ):
                continue

            opname_base = opname[: opname.rfind("_")]

            # The order of opname listed is roughly sorted below

            if opname == "LOAD_ASSERT" and "PyPy" in customize:
                rules_str = """
                stmt ::= JUMP_IF_NOT_DEBUG stmts COME_FROM
                """
                self.add_unique_doc_rules(rules_str, customize)

            elif opname == "BEFORE_ASYNC_WITH":
                rules_str = """
                   stmt            ::= async_with_stmt
                   stmt            ::= async_with_as_stmt
                   c_stmt          ::= c_async_with_stmt
                """

                if self.version < (3, 8):
                    rules_str += """
                      stmt                 ::= async_with_stmt SETUP_ASYNC_WITH
                      c_stmt               ::= c_async_with_stmt SETUP_ASYNC_WITH
                      async_with_stmt      ::= expr
                                               async_with_pre
                                               POP_TOP
                                               suite_stmts_opt
                                               POP_BLOCK LOAD_CONST
                                               async_with_post
                      c_async_with_stmt    ::= expr
                                               async_with_pre
                                               POP_TOP
                                               c_suite_stmts_opt
                                               POP_BLOCK LOAD_CONST
                                               async_with_post
                      async_with_stmt      ::= expr
                                               async_with_pre
                                               POP_TOP
                                               suite_stmts_opt
                                               async_with_post
                      c_async_with_stmt    ::= expr
                                               async_with_pre
                                               POP_TOP
                                               c_suite_stmts_opt
                                               async_with_post
                      async_with_as_stmt   ::= expr
                                               async_with_pre
                                               store
                                               suite_stmts_opt
                                               POP_BLOCK LOAD_CONST
                                               async_with_post
                      c_async_with_as_stmt ::= expr
                                              async_with_pre
                                              store
                                              c_suite_stmts_opt
                                              POP_BLOCK LOAD_CONST
                                              async_with_post
                      async_with_as_stmt   ::= expr
                                              async_with_pre
                                              store
                                              suite_stmts_opt
                                              async_with_post
                      c_async_with_as_stmt ::= expr
                                              async_with_pre
                                              store
                                              suite_stmts_opt
                                              async_with_post
                    """
                else:
                    rules_str += """
                      async_with_pre       ::= BEFORE_ASYNC_WITH GET_AWAITABLE LOAD_CONST YIELD_FROM SETUP_ASYNC_WITH
                      async_with_post      ::= BEGIN_FINALLY COME_FROM_ASYNC_WITH
                                               WITH_CLEANUP_START GET_AWAITABLE LOAD_CONST YIELD_FROM
                                               WITH_CLEANUP_FINISH END_FINALLY
                      async_with_stmt      ::= expr
                                               async_with_pre
                                               POP_TOP
                                               suite_stmts
                                               POP_TOP POP_BLOCK
                                               async_with_post
                      c_async_with_stmt    ::= expr
                                               async_with_pre
                                               POP_TOP
                                               c_suite_stmts
                                               POP_TOP POP_BLOCK
                                               async_with_post
                      c_async_with_stmt   ::= async_with_stmt
                      async_with_stmt     ::= expr
                                              async_with_pre
                                              POP_TOP
                                              c_suite_stmts
                                              POP_BLOCK
                                              BEGIN_FINALLY
                                              WITH_CLEANUP_START GET_AWAITABLE LOAD_CONST YIELD_FROM
                                              WITH_CLEANUP_FINISH POP_FINALLY POP_TOP JUMP_FORWARD
                                              POP_BLOCK
                                              BEGIN_FINALLY
                                              COME_FROM_ASYNC_WITH
                                              WITH_AWAITABLE
                                              LOAD_CONST
                                              YEILD_FROM
                                              WITH_CLEANUP_FINISH
                                              END_FINALLY

                      async_with_as_stmt   ::= expr
                                               async_with_pre
                                               store suite_stmts
                                               POP_TOP POP_BLOCK
                                               async_with_post
                      c_async_with_as_stmt ::= expr
                                               async_with_pre
                                               store suite_stmts
                                               POP_TOP POP_BLOCK
                                               async_with_post
                      async_with_as_stmt   ::= expr
                                               async_with_pre
                                               store suite_stmts
                                               POP_BLOCK async_with_post
                      c_async_with_as_stmt ::= expr
                                               async_with_pre
                                               store suite_stmts
                                               POP_BLOCK async_with_post
                    """
                self.addRule(rules_str, nop_func)

            elif opname == "BUILD_STRING_2":
                self.addRule(
                    """
                      expr                  ::= formatted_value_debug
                      formatted_value_debug ::= LOAD_STR formatted_value2 BUILD_STRING_2
                      formatted_value_debug ::= LOAD_STR formatted_value1 BUILD_STRING_2
                    """,
                    nop_func,
                )
                custom_ops_processed.add(opname)

            elif opname == "BUILD_STRING_3":
                self.addRule(
                    """
                      expr                  ::= formatted_value_debug
                      formatted_value_debug ::= LOAD_STR formatted_value2 LOAD_STR BUILD_STRING_3
                      formatted_value_debug ::= LOAD_STR formatted_value1 LOAD_STR BUILD_STRING_3
                    """,
                    nop_func,
                )
                custom_ops_processed.add(opname)

            elif opname in frozenset(
                (
                    "CALL_FUNCTION",
                    "CALL_FUNCTION_EX_KW",
                    "CALL_FUNCTION_VAR_KW",
                    "CALL_FUNCTION_VAR",
                    "CALL_FUNCTION_VAR_KW",
                )
            ) or opname.startswith("CALL_FUNCTION_KW"):

                if opname == "CALL_FUNCTION" and token.attr == 1:
                    rule = """
                    classdefdeco1 ::= expr classdefdeco2 CALL_FUNCTION_1
                    classdefdeco1 ::= expr classdefdeco1 CALL_FUNCTION_1
                    """
                    self.addRule(rule, nop_func)

                # self.custom_classfunc_rule(opname, token, customize, tokens[i + 1])
                # Note: don't add to custom_ops_processed.

            elif opname_base == "CALL_METHOD":
                # PyPy and Python 3.7+ only - DRY with parse2

                if opname == "CALL_METHOD_KW":
                    args_kw = token.attr
                    rules_str = """
                         expr ::= call_kw_pypy37
                         pypy_kw_keys ::= LOAD_CONST
                    """
                    self.add_unique_doc_rules(rules_str, customize)
                    rule = (
                        "call_kw_pypy37 ::= expr "
                        + ("expr " * args_kw)
                        + " pypy_kw_keys "
                        + opname
                    )
                else:
                    args_pos, args_kw = self.get_pos_kw(token)
                    # number of apply equiv arguments:
                    nak = (len(opname_base) - len("CALL_METHOD")) // 3
                    rule = (
                        "call ::= expr "
                        + ("expr " * args_pos)
                        + ("kwarg " * args_kw)
                        + "expr " * nak
                        + opname
                    )

                self.add_unique_rule(rule, opname, token.attr, customize)

            elif opname == "CONTINUE":
                self.addRule("continue ::= CONTINUE", nop_func)
                custom_ops_processed.add(opname)
            elif opname == "CONTINUE_LOOP":
                self.addRule("continue ::= CONTINUE_LOOP", nop_func)
                custom_ops_processed.add(opname)
            elif opname == "DELETE_ATTR":
                self.addRule("delete ::= expr DELETE_ATTR", nop_func)
                custom_ops_processed.add(opname)
            elif opname == "DELETE_DEREF":
                self.addRule(
                    """
                   stmt           ::= del_deref_stmt
                   del_deref_stmt ::= DELETE_DEREF
                   """,
                    nop_func,
                )
                custom_ops_processed.add(opname)
            elif opname == "DELETE_SUBSCR":
                self.addRule(
                    """
                    delete ::= delete_subscript
                    delete_subscript ::= expr expr DELETE_SUBSCR
                   """,
                    nop_func,
                )
                custom_ops_processed.add(opname)

            elif opname == "FORMAT_VALUE_ATTR":
                self.addRule(
                    """
                      expr                  ::= formatted_value_debug
                      formatted_value_debug ::= LOAD_STR formatted_value2 BUILD_STRING_2
                                                expr FORMAT_VALUE_ATTR
                      formatted_value_debug ::= LOAD_STR formatted_value2 BUILD_STRING_2
                      formatted_value_debug ::= LOAD_STR formatted_value1 BUILD_STRING_2
                    """,
                    nop_func,
                )
                custom_ops_processed.add(opname)

            elif opname == "GET_AITER":
                self.addRule(
                    """
                    async_for          ::= GET_AITER _come_froms
                                           SETUP_FINALLY GET_ANEXT LOAD_CONST YIELD_FROM POP_BLOCK

                    async_for_stmt38   ::= expr async_for
                                           store for_block
                                           COME_FROM_FINALLY
                                           END_ASYNC_FOR

                    # FIXME: COME_FROMs after the else_suite or
                    # END_ASYNC_FOR distinguish which of for / forelse
                    # is used. Add COME_FROMs and check of add up
                    # control-flow detection phase.
                    # async_forelse_stmt38 ::= expr async_for store
                    # for_block COME_FROM_FINALLY END_ASYNC_FOR
                    # else_suite

                    async_forelse_stmt38 ::= expr async_for
                                             store for_block
                                             COME_FROM_FINALLY
                                             END_ASYNC_FOR
                                             else_suite
                                             POP_TOP COME_FROM

                    stmt                 ::= async_for_stmt38
                    stmt                 ::= async_forelse_stmt38
                    stmt                 ::= generator_exp_async
                   """,
                    nop_func,
                )
                custom_ops_processed.add(opname)
            elif opname == "GET_ANEXT":
                self.addRule(
                    """
                    stmt ::= genexpr_func_async
                    stmt ::= BUILD_SET_0 genexpr_func_async
                             RETURN_VALUE
                             _come_froms
                   """,
                    nop_func,
                )
                custom_ops_processed.add(opname)
            elif opname == "JUMP_IF_NOT_DEBUG":
                self.addRule(
                    """
                    stmt        ::= assert_pypy
                    stmt        ::= assert2_pypy", nop_func)
                    assert_pypy ::=  JUMP_IF_NOT_DEBUG expr POP_JUMP_IF_TRUE
                                     LOAD_ASSERT RAISE_VARARGS_1 COME_FROM
                    assert2_pypy ::= JUMP_IF_NOT_DEBUG assert_expr POP_JUMP_IF_TRUE
                                     LOAD_ASSERT expr CALL_FUNCTION_1
                                     RAISE_VARARGS_1 COME_FROM
                    assert2_pypy ::= JUMP_IF_NOT_DEBUG expr POP_JUMP_IF_TRUE
                                     LOAD_ASSERT expr CALL_FUNCTION_1
                                     RAISE_VARARGS_1 COME_FROM,
                    """,
                    nop_func,
                )
                custom_ops_processed.add(opname)

            elif opname == "LOAD_CLASSDEREF":
                # Python 3.4+
                self.addRule("expr ::= LOAD_CLASSDEREF", nop_func)
                custom_ops_processed.add(opname)

            elif opname == "LOAD_CLASSNAME":
                self.addRule("expr ::= LOAD_CLASSNAME", nop_func)
                custom_ops_processed.add(opname)

            elif opname == "RAISE_VARARGS_0":
                self.addRule(
                    """
                    stmt        ::= raise_stmt0
                    last_stmt  ::= raise_stmt0
                    raise_stmt0 ::= RAISE_VARARGS_0
                    """,
                    nop_func,
                )
                custom_ops_processed.add(opname)
            elif opname == "RAISE_VARARGS_1":
                self.addRule(
                    """
                    stmt        ::= raise_stmt1
                    last_stmt  ::= raise_stmt1
                    raise_stmt1 ::= expr RAISE_VARARGS_1
                    """,
                    nop_func,
                )
                custom_ops_processed.add(opname)
            elif opname == "RAISE_VARARGS_2":
                self.addRule(
                    """
                    stmt        ::= raise_stmt2
                    last_stmt  ::= raise_stmt2
                    raise_stmt2 ::= expr expr RAISE_VARARGS_2
                    """,
                    nop_func,
                )
                custom_ops_processed.add(opname)

            elif opname == "RETURN_VALUE_LAMBDA":
                self.addRule(
                    """
                    return_expr_lambda ::= return_expr RETURN_VALUE_LAMBDA
                    """,
                    nop_func,
                )
                custom_ops_processed.add(opname)
            elif opname == "SETUP_EXCEPT":
                self.addRule(
                    """
                    try_except     ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                                       except_handler opt_come_from_except
                    c_try_except   ::= SETUP_EXCEPT c_suite_stmts POP_BLOCK
                                       c_except_handler opt_come_from_except
                    stmt           ::= tryelsestmt3
                    tryelsestmt3   ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                                       except_handler COME_FROM else_suite
                                       opt_come_from_except

                    tryelsestmt    ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                                       except_handler else_suite come_from_except_clauses

                    tryelsestmt    ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                                       except_handler else_suite come_froms

                    c_stmt         ::= c_tryelsestmt
                    c_tryelsestmt  ::= SETUP_EXCEPT c_suite_stmts POP_BLOCK
                                       c_except_handler
                                       come_any_froms else_suitec
                                       come_from_except_clauses
                    """,
                    nop_func,
                )
                custom_ops_processed.add(opname)

            elif opname == "WITH_CLEANUP_START":
                rules_str = """
                  stmt        ::= with_null
                  with_null   ::= with_suffix
                  with_suffix ::= WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY
                """
                self.addRule(rules_str, nop_func)

            # FIXME: reconcile with same code in lambda_custom.py
            elif opname == "SETUP_WITH":
                rules_str = """
                  stmt        ::= with
                  stmt        ::= with_as
                  c_stmt      ::= c_with

                  c_with      ::= expr SETUP_WITH POP_TOP
                                  c_suite_stmts_opt
                                  COME_FROM_WITH
                                  with_suffix
                  c_with      ::= expr SETUP_WITH POP_TOP
                                  c_suite_stmts_opt
                                  POP_BLOCK LOAD_CONST COME_FROM_WITH
                                  with_suffix

                  with        ::= expr SETUP_WITH POP_TOP
                                  suite_stmts_opt
                                  COME_FROM_WITH
                                  with_suffix

                  with_as  ::= expr SETUP_WITH store suite_stmts_opt COME_FROM_WITH
                                  with_suffix

                  with        ::= expr
                                  SETUP_WITH POP_TOP suite_stmts_opt
                                  POP_BLOCK LOAD_CONST COME_FROM_WITH
                                  with_suffix
                  with_as  ::= expr
                                  SETUP_WITH store suite_stmts_opt
                                  POP_BLOCK LOAD_CONST COME_FROM_WITH
                                  with_suffix

                  with        ::= expr
                                  SETUP_WITH POP_TOP suite_stmts_opt
                                  POP_BLOCK LOAD_CONST COME_FROM_WITH
                                  with_suffix
                  with_as  ::= expr
                                  SETUP_WITH store suite_stmts_opt
                                  POP_BLOCK LOAD_CONST COME_FROM_WITH
                                  with_suffix
                """
                if self.version < (3, 8):
                    rules_str += """
                    with      ::= expr SETUP_WITH POP_TOP suite_stmts_opt POP_BLOCK
                                   LOAD_CONST
                                   with_suffix
                    """
                else:
                    rules_str += """
                     # A return at the end of a withas stmt can be this.
                     # FIXME: should this be a different kind of return?
                     return      ::= return_expr POP_BLOCK
                                     ROT_TWO
                                     BEGIN_FINALLY
                                     WITH_CLEANUP_START
                                     WITH_CLEANUP_FINISH
                                     POP_FINALLY
                                     RETURN_VALUE

                      with       ::= expr
                                     SETUP_WITH POP_TOP suite_stmts_opt
                                     POP_BLOCK LOAD_CONST COME_FROM_WITH
                                     with_suffix


                      with_as    ::= expr
                                     SETUP_WITH store suite_stmts
                                     POP_BLOCK LOAD_CONST COME_FROM_WITH

                      with_as    ::= expr
                                     SETUP_WITH store suite_stmts
                                     POP_BLOCK BEGIN_FINALLY COME_FROM_WITH
                                     with_suffix

                      # with_as ::= expr SETUP_WITH store suite_stmts
                      #                COME_FROM expr COME_FROM POP_BLOCK ROT_TWO
                      #                BEGIN_FINALLY WITH_CLEANUP_START WITH_CLEANUP_FINISH
                      #                POP_FINALLY RETURN_VALUE COME_FROM_WITH
                      #                WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY

                      with         ::= expr SETUP_WITH POP_TOP suite_stmts_opt POP_BLOCK
                                       BEGIN_FINALLY COME_FROM_WITH
                                       with_suffix
                    """
                self.addRule(rules_str, nop_func)
            pass

        return

    def customize_reduce_checks_full38(self, tokens, customize):
        """
        Extra tests when a reduction is made in the full grammar.

        Reductions here are extended from those used in the lambda grammar
        """
        self.remove_rules_38()

        self.check_reduce["and"] = "AST"
        self.check_reduce["and_cond"] = "AST"
        self.check_reduce["and_not"] = "AST"
        self.check_reduce["annotate_tuple"] = "tokens"
        self.check_reduce["aug_assign1"] = "AST"
        self.check_reduce["aug_assign2"] = "AST"
        self.check_reduce["c_forelsestmt38"] = "AST"
        self.check_reduce["c_try_except"] = "AST"
        self.check_reduce["c_tryelsestmt"] = "AST"
        self.check_reduce["if_and_stmt"] = "AST"
        self.check_reduce["if_and_elsestmtc"] = "AST"
        self.check_reduce["if_not_stmtc"] = "AST"
        self.check_reduce["ifelsestmt"] = "AST"
        self.check_reduce["ifelsestmtc"] = "AST"
        self.check_reduce["iflaststmt"] = "AST"
        self.check_reduce["iflaststmtc"] = "AST"
        self.check_reduce["ifstmt"] = "AST"
        self.check_reduce["ifstmtc"] = "AST"
        self.check_reduce["ifstmts_jump"] = "AST"
        self.check_reduce["ifstmts_jumpc"] = "AST"
        self.check_reduce["import_as37"] = "tokens"
        self.check_reduce["import_from37"] = "AST"
        self.check_reduce["import_from_as37"] = "tokens"
        self.check_reduce["lastc_stmt"] = "tokens"
        self.check_reduce["list_if_not"] = "AST"
        self.check_reduce["while1elsestmt"] = "tokens"
        self.check_reduce["while1stmt"] = "tokens"
        self.check_reduce["whilestmt"] = "tokens"
        self.check_reduce["not_or"] = "AST"
        self.check_reduce["or"] = "AST"
        self.check_reduce["or_cond"] = "tokens"
        self.check_reduce["testtrue"] = "tokens"
        self.check_reduce["testfalsec"] = "tokens"

        self.check_reduce["break"] = "tokens"
        self.check_reduce["forelselaststmt38"] = "AST"
        self.check_reduce["forelselaststmtc38"] = "AST"
        self.check_reduce["for38"] = "tokens"
        self.check_reduce["ifstmt"] = "AST"
        self.check_reduce["joined_str"] = "AST"
        self.check_reduce["pop_return"] = "tokens"
        self.check_reduce["whileTruestmt38"] = "AST"
        self.check_reduce["whilestmt38"] = "tokens"
        self.check_reduce["try_elsestmtl38"] = "AST"

        self.reduce_check_table["break"] = break_invalid
        self.reduce_check_table["if_not_stmtc"] = if_not_stmtc_invalid
        self.reduce_check_table["for38"] = for38_invalid
        self.reduce_check_table["c_forelsestmt38"] = forelse38_invalid
        self.reduce_check_table["forelselaststmt38"] = forelse38_invalid
        self.reduce_check_table["forelselaststmtc38"] = forelse38_invalid
        # self.reduce_check_table["joined_str"] = joined_str_check.joined_str_invalid
        self.reduce_check_table["or"] = or_cond_check_invalid
        self.reduce_check_table["pop_return"] = pop_return_check
        self.reduce_check_table["whilestmt38"] = whilestmt38_check
        self.reduce_check_table["whileTruestmt38"] = whileTruestmt38_check

        # Use update we don't destroy entries from lambda.
        self.reduce_check_table.update(
            {
                # "ifelsestmt": ifelsestmt_ok,
                "ifstmt": ifstmt,
                # "import_from37": import_from37_ok,
            }
        )

        self.check_reduce["ifelsestmt"] = "AST"
        self.check_reduce["ifelsestmtc"] = "AST"
        self.check_reduce["ifstmt"] = "AST"
        # self.check_reduce["import_from37"] = "AST"

    def customize_grammar_rules38(self, tokens, customize):
        Python37BaseParser.customize_grammar_rules37(self, tokens, customize)
        self.customize_reduce_checks_lambda38()
        self.customize_reduce_checks_full38(tokens, customize)

        # include instructions that don't need customization,
        # but we'll do a finer check after the rough breakout.
        customize_instruction_basenames = frozenset(
            (
                "BEFORE",
                "BUILD",
                "CALL",
                "CONTINUE",
                "DELETE",
                "FORMAT",
                "GET",
                "JUMP",
                "LOAD",
                "LOOKUP",
                "MAKE",
                "RETURN",
                "RAISE",
                "SETUP",
                "UNPACK",
                "WITH",
            )
        )

        # Opcode names in the custom_ops_processed set have rules that get added
        # unconditionally and the rules are constant. So they need to be done
        # only once and if we see the opcode a second we don't have to consider
        # adding more rules.
        #
        custom_ops_processed = set()

        # A set of instruction operation names that exist in the token stream.
        # We use this to customize the grammar that we create.
        # 2.6-compatible set comprehensions

        # The initial initialization is done in lambda_expr.py
        self.seen_ops = frozenset([t.kind for t in tokens])
        self.seen_op_basenames = frozenset(
            [opname[: opname.rfind("_")] for opname in self.seen_ops]
        )

        # Loop over instructions adding custom grammar rules based on
        # a specific instruction seen.

        if "PyPy" in customize:
            self.addRule(
                """
              stmt ::= assign3_pypy
              stmt ::= assign2_pypy
              assign3_pypy       ::= expr expr expr store store store
              assign2_pypy       ::= expr expr store store
              """,
                nop_func,
            )

        for i, token in enumerate(tokens):
            opname = token.kind

            # Do a quick breakout before testing potentially
            # each of the dozen or so instruction in if elif.
            if (
                opname[: opname.find("_")] not in customize_instruction_basenames
                or opname in custom_ops_processed
            ):
                continue

            opname_base = opname[: opname.rfind("_")]

            # The order of opname listed is roughly sorted below

            if opname == "LOAD_ASSERT" and "PyPy" in customize:
                rules_str = """
                stmt ::= JUMP_IF_NOT_DEBUG stmts COME_FROM
                """
                self.add_unique_doc_rules(rules_str, customize)

            elif opname == "BEFORE_ASYNC_WITH":
                rules_str = """
                   stmt            ::= async_with_stmt
                   stmt            ::= async_with_as_stmt
                   c_stmt          ::= c_async_with_stmt
                """
                if self.version < (3, 8):
                    rules_str += """
                      async_with_pre       ::= BEFORE_ASYNC_WITH GET_AWAITABLE LOAD_CONST YIELD_FROM
                                               SETUP_ASYNC_WITH
                      stmt                 ::= async_with_stmt SETUP_ASYNC_WITH
                      c_stmt               ::= c_async_with_stmt SETUP_ASYNC_WITH
                      async_with_stmt      ::= expr
                                               async_with_pre
                                               POP_TOP
                                               suite_stmts_opt
                                               POP_BLOCK LOAD_CONST
                                               async_with_post
                      c_async_with_stmt    ::= expr
                                               async_with_pre
                                               POP_TOP
                                               c_suite_stmts_opt
                                               POP_BLOCK LOAD_CONST
                                               async_with_post
                      async_with_stmt      ::= expr
                                               async_with_pre
                                               POP_TOP
                                               suite_stmts_opt
                                               async_with_post
                      c_async_with_stmt    ::= expr
                                               async_with_pre
                                               POP_TOP
                                               c_suite_stmts_opt
                                               async_with_post
                      async_with_as_stmt   ::= expr
                                               async_with_pre
                                               store
                                               suite_stmts_opt
                                               POP_BLOCK LOAD_CONST
                                               async_with_post
                      c_async_with_as_stmt ::= expr
                                              async_with_pre
                                              store
                                              c_suite_stmts_opt
                                              POP_BLOCK LOAD_CONST
                                              async_with_post
                      async_with_as_stmt   ::= expr
                                              async_with_pre
                                              store
                                              suite_stmts_opt
                                              async_with_post
                      c_async_with_as_stmt ::= expr
                                              async_with_pre
                                              store
                                              suite_stmts_opt
                                              async_with_post
                    """
                else:
                    rules_str += """
                      async_with_pre       ::= BEFORE_ASYNC_WITH GET_AWAITABLE LOAD_CONST YIELD_FROM SETUP_ASYNC_WITH
                      async_with_post      ::= BEGIN_FINALLY COME_FROM_ASYNC_WITH
                                               WITH_CLEANUP_START GET_AWAITABLE LOAD_CONST YIELD_FROM
                                               WITH_CLEANUP_FINISH END_FINALLY
                      async_with_stmt      ::= expr
                                               async_with_pre
                                               POP_TOP
                                               suite_stmts
                                               POP_TOP POP_BLOCK
                                               async_with_post
                      c_async_with_stmt    ::= expr
                                               async_with_pre
                                               POP_TOP
                                               c_suite_stmts
                                               POP_TOP POP_BLOCK
                                               async_with_post
                      c_async_with_stmt   ::= async_with_stmt
                      async_with_stmt     ::= expr
                                              async_with_pre
                                              POP_TOP
                                              c_suite_stmts
                                              POP_BLOCK
                                              BEGIN_FINALLY
                                              WITH_CLEANUP_START GET_AWAITABLE LOAD_CONST YIELD_FROM
                                              WITH_CLEANUP_FINISH POP_FINALLY POP_TOP JUMP_FORWARD
                                              POP_BLOCK
                                              BEGIN_FINALLY
                                              COME_FROM_ASYNC_WITH
                                              WITH_AWAITABLE
                                              LOAD_CONST
                                              YEILD_FROM
                                              WITH_CLEANUP_FINISH
                                              END_FINALLY

                      async_with_as_stmt   ::= expr
                                               async_with_pre
                                               store suite_stmts
                                               POP_TOP POP_BLOCK
                                               async_with_post
                      c_async_with_as_stmt ::= expr
                                               async_with_pre
                                               store suite_stmts
                                               POP_TOP POP_BLOCK
                                               async_with_post
                      async_with_as_stmt   ::= expr
                                               async_with_pre
                                               store suite_stmts
                                               POP_BLOCK async_with_post
                      c_async_with_as_stmt ::= expr
                                               async_with_pre
                                               store suite_stmts
                                               POP_BLOCK async_with_post
                    """
                self.addRule(rules_str, nop_func)

            elif opname in frozenset(
                (
                    "CALL_FUNCTION",
                    "CALL_FUNCTION_EX_KW",
                    "CALL_FUNCTION_VAR_KW",
                    "CALL_FUNCTION_VAR",
                    "CALL_FUNCTION_VAR_KW",
                )
            ) or opname.startswith("CALL_FUNCTION_KW"):

                if opname == "CALL_FUNCTION" and token.attr == 1:
                    rule = """
                    classdefdeco1 ::= expr classdefdeco2 CALL_FUNCTION_1
                    classdefdeco1 ::= expr classdefdeco1 CALL_FUNCTION_1
                    """
                    self.addRule(rule, nop_func)

                # self.custom_classfunc_rule(opname, token, customize, tokens[i + 1])
                # Note: don't add to custom_ops_processed.

            elif opname_base == "CALL_METHOD":
                # PyPy and Python 3.7+ only - DRY with parse2

                if opname == "CALL_METHOD_KW":
                    args_kw = token.attr
                    rules_str = """
                         expr ::= call_kw_pypy37
                         pypy_kw_keys ::= LOAD_CONST
                    """
                    self.add_unique_doc_rules(rules_str, customize)
                    rule = (
                        "call_kw_pypy37 ::= expr "
                        + ("expr " * args_kw)
                        + " pypy_kw_keys "
                        + opname
                    )
                else:
                    args_pos, args_kw = self.get_pos_kw(token)
                    # number of apply equiv arguments:
                    nak = (len(opname_base) - len("CALL_METHOD")) // 3
                    rule = (
                        "call ::= expr "
                        + ("expr " * args_pos)
                        + ("kwarg " * args_kw)
                        + "expr " * nak
                        + opname
                    )

                self.add_unique_rule(rule, opname, token.attr, customize)

            elif opname == "CONTINUE":
                self.addRule("continue ::= CONTINUE", nop_func)
                custom_ops_processed.add(opname)
            elif opname == "CONTINUE_LOOP":
                self.addRule("continue ::= CONTINUE_LOOP", nop_func)
                custom_ops_processed.add(opname)
            elif opname == "DELETE_ATTR":
                self.addRule("delete ::= expr DELETE_ATTR", nop_func)
                custom_ops_processed.add(opname)
            elif opname == "DELETE_DEREF":
                self.addRule(
                    """
                   stmt           ::= del_deref_stmt
                   del_deref_stmt ::= DELETE_DEREF
                   """,
                    nop_func,
                )
                custom_ops_processed.add(opname)
            elif opname == "DELETE_SUBSCR":
                self.addRule(
                    """
                    delete ::= delete_subscript
                    delete_subscript ::= expr expr DELETE_SUBSCR
                   """,
                    nop_func,
                )
                custom_ops_processed.add(opname)

            elif opname == "GET_AITER":
                self.addRule(
                    """
                    stmt ::= generator_exp_async
                    stmt ::= genexpr_func_async
                   """,
                    nop_func,
                )
                custom_ops_processed.add(opname)
            elif opname == "GET_ANEXT":
                self.addRule(
                    """
                    stmt ::= BUILD_SET_0 genexpr_func_async
                             RETURN_VALUE
                             bb_doms_end_opt
                   """,
                    nop_func,
                )
                custom_ops_processed.add(opname)
            elif opname == "JUMP_IF_NOT_DEBUG":
                self.addRule(
                    """
                    stmt        ::= assert_pypy
                    stmt        ::= assert2_pypy", nop_func)
                    assert_pypy ::=  JUMP_IF_NOT_DEBUG expr POP_JUMP_IF_TRUE
                                     LOAD_ASSERT RAISE_VARARGS_1 COME_FROM
                    assert2_pypy ::= JUMP_IF_NOT_DEBUG assert_expr POP_JUMP_IF_TRUE
                                     LOAD_ASSERT expr CALL_FUNCTION_1
                                     RAISE_VARARGS_1 COME_FROM
                    assert2_pypy ::= JUMP_IF_NOT_DEBUG expr POP_JUMP_IF_TRUE
                                     LOAD_ASSERT expr CALL_FUNCTION_1
                                     RAISE_VARARGS_1 COME_FROM,
                    """,
                    nop_func,
                )
                custom_ops_processed.add(opname)

            elif opname == "LOAD_CLASSDEREF":
                # Python 3.4+
                self.addRule("expr ::= LOAD_CLASSDEREF", nop_func)
                custom_ops_processed.add(opname)

            elif opname == "LOAD_CLASSNAME":
                self.addRule("expr ::= LOAD_CLASSNAME", nop_func)
                custom_ops_processed.add(opname)

            elif opname == "RAISE_VARARGS_0":
                self.addRule(
                    """
                    stmt        ::= raise_stmt0
                    last_stmt  ::= raise_stmt0
                    raise_stmt0 ::= RAISE_VARARGS_0
                    """,
                    nop_func,
                )
                custom_ops_processed.add(opname)
            elif opname == "RAISE_VARARGS_1":
                self.addRule(
                    """
                    stmt        ::= raise_stmt1
                    last_stmt  ::= raise_stmt1
                    raise_stmt1 ::= expr RAISE_VARARGS_1
                    """,
                    nop_func,
                )
                custom_ops_processed.add(opname)
            elif opname == "RAISE_VARARGS_2":
                self.addRule(
                    """
                    stmt        ::= raise_stmt2
                    last_stmt  ::= raise_stmt2
                    raise_stmt2 ::= expr expr RAISE_VARARGS_2
                    """,
                    nop_func,
                )
                custom_ops_processed.add(opname)

            elif opname == "RETURN_VALUE_LAMBDA":
                self.addRule(
                    """
                    return_expr_lambda ::= return_expr RETURN_VALUE_LAMBDA
                    """,
                    nop_func,
                )
                custom_ops_processed.add(opname)
            elif opname == "SETUP_EXCEPT":
                self.addRule(
                    """
                    try_except     ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                                       except_handler opt_come_from_except
                    c_try_except   ::= SETUP_EXCEPT c_suite_stmts POP_BLOCK
                                       c_except_handler opt_come_from_except
                    stmt           ::= tryelsestmt3
                    tryelsestmt3   ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                                       except_handler COME_FROM else_suite
                                       opt_come_from_except

                    tryelsestmt    ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                                       except_handler else_suite come_from_except_clauses

                    tryelsestmt    ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                                       except_handler else_suite come_froms

                    c_stmt         ::= c_tryelsestmt
                    c_tryelsestmt  ::= SETUP_EXCEPT c_suite_stmts POP_BLOCK
                                       c_except_handler
                                       come_any_froms else_suitec
                                       come_from_except_clauses
                    """,
                    nop_func,
                )
                custom_ops_processed.add(opname)

            elif opname == "WITH_CLEANUP_START":
                rules_str = """
                  stmt        ::= with_null
                  with_null   ::= with_suffix
                  with_suffix ::= WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY
                """
                self.addRule(rules_str, nop_func)

            # FIXME: reconcile with same code in lambda_custom.py
            elif opname == "SETUP_WITH":
                rules_str = """
                  stmt        ::= with
                  stmt        ::= with_as
                  c_stmt      ::= c_with

                  c_with      ::= expr SETUP_WITH POP_TOP
                                  c_suite_stmts_opt
                                  COME_FROM_WITH
                                  with_suffix
                  c_with      ::= expr SETUP_WITH POP_TOP
                                  c_suite_stmts_opt
                                  POP_BLOCK LOAD_CONST COME_FROM_WITH
                                  with_suffix

                  with        ::= expr SETUP_WITH POP_TOP
                                  suite_stmts_opt
                                  COME_FROM_WITH
                                  with_suffix

                  with_as  ::= expr SETUP_WITH store suite_stmts_opt COME_FROM_WITH
                                  with_suffix

                  with        ::= expr
                                  SETUP_WITH POP_TOP suite_stmts_opt
                                  POP_BLOCK LOAD_CONST COME_FROM_WITH
                                  with_suffix
                  with_as     ::= expr
                                  SETUP_WITH store suite_stmts_opt
                                  POP_BLOCK LOAD_CONST COME_FROM_WITH
                                  with_suffix

                  with        ::= expr
                                  SETUP_WITH POP_TOP suite_stmts_opt
                                  POP_BLOCK LOAD_CONST COME_FROM_WITH
                                  with_suffix
                  with_as  ::= expr
                                  SETUP_WITH store suite_stmts_opt
                                  POP_BLOCK LOAD_CONST COME_FROM_WITH
                                  with_suffix
                """
                if self.version < (3, 8):
                    rules_str += """
                    with      ::= expr SETUP_WITH POP_TOP suite_stmts_opt POP_BLOCK
                                   LOAD_CONST
                                   with_suffix
                    """
                else:
                    rules_str += """
                     # A return at the end of a withas stmt can be this.
                     # FIXME: should this be a different kind of return?
                     return      ::= return_expr POP_BLOCK
                                     ROT_TWO
                                     BEGIN_FINALLY
                                     WITH_CLEANUP_START
                                     WITH_CLEANUP_FINISH
                                     POP_FINALLY
                                     RETURN_VALUE

                      with       ::= expr
                                     SETUP_WITH POP_TOP suite_stmts_opt
                                     POP_BLOCK LOAD_CONST COME_FROM_WITH
                                     with_suffix


                      with_as    ::= expr
                                     SETUP_WITH store suite_stmts
                                     POP_BLOCK LOAD_CONST COME_FROM_WITH

                      with_as    ::= expr
                                     SETUP_WITH store suite_stmts
                                     POP_BLOCK BEGIN_FINALLY COME_FROM_WITH
                                     with_suffix

                      # with_as   ::= expr SETUP_WITH store suite_stmts
                      #               COME_FROM expr COME_FROM POP_BLOCK ROT_TWO
                      #               BEGIN_FINALLY WITH_CLEANUP_START WITH_CLEANUP_FINISH
                      #               POP_FINALLY RETURN_VALUE COME_FROM_WITH
                      #               WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY

                      with         ::= expr SETUP_WITH POP_TOP suite_stmts_opt POP_BLOCK
                                       BEGIN_FINALLY COME_FROM_WITH
                                       with_suffix
                    """
                self.addRule(rules_str, nop_func)
            pass

        return
