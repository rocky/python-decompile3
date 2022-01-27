#  Copyright (c) 2020-2022 Rocky Bernstein
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
Grammar Customization rules for Python 3.7's Lambda expression grammar.
"""

from decompyle3.parsers.p37.base import Python37BaseParser
from decompyle3.parsers.parse_heads import nop_func


class Python37LambdaCustom(Python37BaseParser):
    def __init__(self):
        self.new_rules = set()
        self.customized = {}

    def customize_grammar_rules_lambda37(self, tokens, customize):
        Python37BaseParser.customize_grammar_rules37(self, tokens, customize)
        self.check_reduce["call_kw"] = "AST"

        # For a rough break out on the first word. This may
        # include instructions that don't need customization,
        # but we'll do a finer check after the rough breakout.
        customize_instruction_basenames = frozenset(
            (
                "BEFORE",
                "BUILD",
                "CALL",
                "DICT",
                "GET",
                "FORMAT",
                "LIST",
                "LOAD",
                "MAKE",
                "SETUP",
                "UNPACK",
            )
        )

        # Opcode names in the custom_ops_processed set have rules that get added
        # unconditionally and the rules are constant. So they need to be done
        # only once and if we see the opcode a second we don't have to consider
        # adding more rules.
        #
        # Note: BUILD_TUPLE_UNPACK_WITH_CALL gets considered by
        # default because it starts with BUILD. So we'll set to ignore it from
        # the start.
        custom_ops_processed = set(("BUILD_TUPLE_UNPACK_WITH_CALL",))

        for i, token in enumerate(tokens):
            opname = token.kind

            opname_base = opname[: opname.rfind("_")]

            # Do a quick breakout before testing potentially
            # each of the dozen or so instruction in if elif.
            if (
                opname[: opname.find("_")] not in customize_instruction_basenames
                or opname in custom_ops_processed
            ):
                continue

            if opname_base == "BUILD_LIST":
                v = token.attr
                if v == 0:
                    rule_str = """
                       list        ::= BUILD_LIST_0
                       list_unpack ::= BUILD_LIST_0 expr LIST_EXTEND
                       list        ::= list_unpack
                    """
                    self.add_unique_doc_rules(rule_str, customize)
                else:
                    rule_str = f"""
                     list  ::= {'expr ' * v}{opname}
                    """
                    self.add_unique_doc_rules(rule_str, customize)

            elif opname_base == "BUILD_STRING":
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

            elif opname_base == "BUILD_MAP_UNPACK_WITH_CALL":
                v = token.attr
                rule = "build_map_unpack_with_call ::= %s%s" % ("expr " * v, opname)
                self.addRule(rule, nop_func)

            elif opname_base == "BUILD_TUPLE_UNPACK_WITH_CALL":
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

            elif opname == "GET_AITER":
                self.addRule(
                    """
                    expr                ::= generator_exp_async
                    expr                ::= list_comp_async

                    func_async_middle   ::= POP_BLOCK JUMP_FORWARD COME_FROM_EXCEPT
                                            DUP_TOP LOAD_GLOBAL COMPARE_OP POP_JUMP_IF_TRUE
                                            END_FINALLY COME_FROM

                    func_async_prefix   ::= _come_froms SETUP_EXCEPT GET_ANEXT LOAD_CONST YIELD_FROM

                    generator_exp_async ::= load_genexpr LOAD_STR MAKE_FUNCTION_0 expr
                                            GET_AITER CALL_FUNCTION_1

                    genexpr_func_async  ::= LOAD_ARG func_async_prefix
                                            store func_async_middle comp_iter
                                            JUMP_LOOP COME_FROM
                                            POP_TOP POP_TOP POP_TOP POP_EXCEPT POP_TOP

                    get_aiter           ::= expr GET_AITER

                    list_afor           ::= get_aiter list_afor2

                    list_afor2          ::= func_async_prefix
                                            store func_async_middle list_iter
                                            JUMP_LOOP COME_FROM
                                            POP_TOP POP_TOP POP_TOP POP_EXCEPT POP_TOP

                    list_comp_async     ::= BUILD_LIST_0 LOAD_ARG list_afor2
                    list_comp_async     ::= LOAD_LISTCOMP LOAD_STR MAKE_FUNCTION_0
                                            expr GET_AITER CALL_FUNCTION_1
                                            GET_AWAITABLE LOAD_CONST
                                            YIELD_FROM

                    list_iter           ::= list_afor
                   """,
                    nop_func,
                )
                custom_ops_processed.add(opname)

            elif opname == "GET_AWAITABLE":
                rule_str = """
                    await_expr ::= expr GET_AWAITABLE LOAD_CONST YIELD_FROM
                    expr       ::= await_expr
                """
                self.add_unique_doc_rules(rule_str, customize)

            elif opname == "GET_ITER":
                self.addRule(
                    """
                    expr      ::= get_iter
                    get_iter  ::= expr GET_ITER
                    """,
                    nop_func,
                )
                custom_ops_processed.add(opname)

            elif opname == "LOAD_ASSERT":
                if "PyPy" in customize:
                    rules_str = """
                    stmt ::= JUMP_IF_NOT_DEBUG stmts COME_FROM
                    """
                    self.add_unique_doc_rules(rules_str, customize)

            elif opname == "LOAD_ATTR":
                self.addRule(
                    """
                  expr      ::= attribute
                  attribute ::= expr LOAD_ATTR
                  """,
                    nop_func,
                )
                custom_ops_processed.add(opname)

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

            elif opname == "MAKE_FUNCTION_9":
                args_pos, args_kw, annotate_args, closure = token.attr
                stack_count = args_pos + args_kw + annotate_args
                if args_pos:
                    # This was seen ion line 447 of Python 3.8
                    # This is needed for Python 3.8 line 447 of site-packages/nltk/tgrep.py
                    # line 447:
                    #    lambda i: lambda n, m=None, l=None: ...
                    # which has
                    #  L. 447         0  LOAD_CONST               (None, None)
                    #                 2  LOAD_CLOSURE             'i'
                    #                 4  LOAD_CLOSURE             'predicate'
                    #                 6  BUILD_TUPLE_2         2
                    #                 8  LOAD_LAMBDA              '<code_object <lambda>>'
                    #                10  LOAD_STR                 '_tgrep_relation_action.<locals>.<lambda>.<locals>.<lambda>'
                    #                12  MAKE_FUNCTION_9          'default, closure'
                    # FIXME: Possibly we need to generalize for more nested lambda's of lambda's?
                    rule = """
                         expr        ::= lambda_body
                         lambda_body ::= %s%s%s%s
                         """ % (
                        "expr " * stack_count,
                        "load_closure " * closure,
                        "LOAD_LAMBDA LOAD_STR ",
                        opname,
                    )
                    self.add_unique_rule(rule, opname, token.attr, customize)

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

            elif opname == "SETUP_WITH":
                rules_str = """
                with       ::= expr SETUP_WITH POP_TOP suite_stmts_opt COME_FROM_WITH
                               WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY

                # Removes POP_BLOCK LOAD_CONST from 3.6-
                withasstmt ::= expr SETUP_WITH store suite_stmts_opt COME_FROM_WITH
                               WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY
                """
                if self.version < (3, 8):
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
            # Note that we don't add to customize token.kind here. Instead, the non-terminal
            # names call_ex_kw... are is in semantic actions.
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
            Python37BaseParser.custom_classfunc_rule(
                self, opname, token, customize, next_token
            )
