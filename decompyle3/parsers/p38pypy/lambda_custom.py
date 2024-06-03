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
Grammar Customization rules for Python 3.8's Lambda expression grammar.
"""

from decompyle3.parsers.p37.base import Python37BaseParser
from decompyle3.parsers.p38pypy.base import Python38PyPyBaseParser
from decompyle3.parsers.parse_heads import nop_func


class Python38PyPyLambdaCustom(Python38PyPyBaseParser):
    def __init__(self):
        self.new_rules = set()
        self.customized = {}

    def remove_rules_pypy38(self):
        self.remove_rules(
            """
            """
        )

    def customize_grammar_rules_lambda38(self, tokens, customize):
        Python38PyPyBaseParser.customize_grammar_rules38(self, tokens, customize)

        # self.remove_rules_pypy38()
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
        custom_ops_processed = frozenset()

        # A set of instruction operation names that exist in the token stream.
        # We use this customize the grammar that we create.
        # 2.6-compatible set comprehensions
        self.seen_ops = frozenset([t.kind for t in tokens])
        self.seen_op_basenames = frozenset(
            [opname[: opname.rfind("_")] for opname in self.seen_ops]
        )

        custom_ops_processed = {"DICT_MERGE"}

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

        n = len(tokens)

        # Determine if we have an iteration CALL_FUNCTION_1.
        has_get_iter_call_function1 = False
        for i, token in enumerate(tokens):
            if (
                token == "GET_ITER"
                and i < n - 2
                and self.call_fn_name(tokens[i + 1]) == "CALL_FUNCTION_1"
            ):
                has_get_iter_call_function1 = True

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

            # Do a quick breakout before testing potentially
            # each of the dozen or so instruction in if elif.
            if (
                opname[: opname.find("_")] not in customize_instruction_basenames
                or opname in custom_ops_processed
            ):
                continue

            if opname == "BEFORE_ASYNC_WITH":
                rules_str = """
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
                                          c_suite_stmts
                                          POP_BLOCK
                                          BEGIN_FINALLY
                                          WITH_CLEANUP_START GET_AWAITABLE LOAD_CONST YIELD_FROM
                                          WITH_CLEANUP_FINISH POP_FINALLY POP_TOP JUMP_FORWARD
                                          POP_BLOCK
                                          BEGIN_FINALLY
                                          COME_FROM_ASYNC_WITH
                                          WITH_CLEANUP_START
                                          GET_AWAITABLE
                                          LOAD_CONST
                                          YIELD_FROM
                                          WITH_CLEANUP_FINISH
                                          END_FINALLY


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

            elif opname in ("BUILD_CONST_LIST", "BUILD_CONST_DICT", "BUILD_CONST_SET"):
                if opname == "BUILD_CONST_DICT":
                    rule = f"""
                            add_consts          ::= ADD_VALUE*
                            const_list          ::= COLLECTION_START add_consts {opname}
                            dict                ::= const_list
                            expr                ::= dict
                        """
                else:
                    rule = f"""
                            add_consts          ::= ADD_VALUE*
                            const_list          ::= COLLECTION_START add_consts {opname}
                            expr                ::= const_list
                        """
                self.addRule(rule, nop_func)
            elif opname_base in (
                "BUILD_LIST",
                "BUILD_SET",
                "BUILD_SET_UNPACK",
                "BUILD_TUPLE",
                "BUILD_TUPLE_UNPACK",
            ):
                v = token.attr

                is_LOAD_CLOSURE = False
                if opname_base == "BUILD_TUPLE":
                    # If is part of a "load_closure", then it is not part of a
                    # "list".
                    is_LOAD_CLOSURE = True
                    for j in range(v):
                        if tokens[i - j - 1].kind != "LOAD_CLOSURE":
                            is_LOAD_CLOSURE = False
                            break
                    if is_LOAD_CLOSURE:
                        rule = "load_closure ::= %s%s" % (("LOAD_CLOSURE " * v), opname)
                        self.add_unique_rule(rule, opname, token.attr, customize)

                elif opname_base == "BUILD_LIST":
                    v = token.attr
                    if v == 0:
                        rule_str = """
                           list        ::= BUILD_LIST_0
                           list_unpack ::= BUILD_LIST_0 expr LIST_EXTEND
                           list        ::= list_unpack
                        """
                        self.add_unique_doc_rules(rule_str, customize)

                elif opname == "BUILD_TUPLE_UNPACK_WITH_CALL":
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

                if not is_LOAD_CLOSURE or v == 0:
                    # We do this complicated test to speed up parsing of
                    # pathelogically long literals, especially those over 1024.
                    build_count = token.attr
                    thousands = build_count // 1024
                    thirty32s = (build_count // 32) % 32
                    if thirty32s > 0:
                        rule = "expr32 ::=%s" % (" expr" * 32)
                        self.add_unique_rule(rule, opname_base, build_count, customize)
                        pass
                    if thousands > 0:
                        self.add_unique_rule(
                            "expr1024 ::=%s" % (" expr32" * 32),
                            opname_base,
                            build_count,
                            customize,
                        )
                        pass
                    collection = opname_base[opname_base.find("_") + 1 :].lower()
                    rule = (
                        ("%s ::= " % collection)
                        + "expr1024 " * thousands
                        + "expr32 " * thirty32s
                        + "expr " * (build_count % 32)
                        + opname
                    )
                    self.add_unique_rules(["expr ::= %s" % collection, rule], customize)
                    continue
                continue

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
                self.add_unique_doc_rules("get_aiter ::= expr GET_AITER", customize)

                if not {"MAKE_FUNCTION_0", "MAKE_FUNCTION_CLOSURE"} in self.seen_ops:
                    self.addRule(
                        """
                        expr                ::= dict_comp_async
                        expr                ::= generator_exp_async
                        expr                ::= list_comp_async

                        dict_comp_async     ::= LOAD_DICTCOMP
                                                LOAD_STR
                                                MAKE_FUNCTION_0
                                                get_aiter
                                                CALL_FUNCTION_1

                        dict_comp_async     ::= BUILD_MAP_0 LOAD_ARG
                                                dict_comp_async

                        generator_exp_async ::= load_genexpr LOAD_STR MAKE_FUNCTION_0
                                                get_aiter CALL_FUNCTION_1

                        list_comp_async     ::= LOAD_LISTCOMP LOAD_STR MAKE_FUNCTION_0
                                                get_aiter CALL_FUNCTION_1
                                                await

                        list_comp_async     ::= LOAD_CLOSURE
                                                BUILD_TUPLE_1
                                                LOAD_LISTCOMP
                                                LOAD_STR MAKE_FUNCTION_CLOSURE
                                                get_aiter CALL_FUNCTION_1
                                                await

                        set_comp_async       ::= LOAD_SETCOMP
                                                 LOAD_STR
                                                 MAKE_FUNCTION_0
                                                 get_aiter
                                                 CALL_FUNCTION_1

                        set_comp_async       ::= LOAD_CLOSURE
                                                 BUILD_TUPLE_1
                                                 LOAD_SETCOMP
                                                 LOAD_STR MAKE_FUNCTION_CLOSURE
                                                 get_aiter CALL_FUNCTION_1
                                                 await
                       """,
                        nop_func,
                    )
                    custom_ops_processed.add(opname)

                self.addRule(
                    """
                    dict_comp_async      ::= BUILD_MAP_0 LOAD_ARG
                                             dict_comp_async

                    expr                 ::= dict_comp_async
                    expr                 ::= generator_exp_async
                    expr                 ::= list_comp_async
                    expr                 ::= set_comp_async

                    func_async_middle   ::= POP_BLOCK JUMP_FORWARD COME_FROM_EXCEPT
                                            DUP_TOP LOAD_GLOBAL COMPARE_OP
                                            POP_JUMP_IF_TRUE
                                            END_FINALLY _come_froms

                    # async_iter         ::= block_break SETUP_EXCEPT GET_ANEXT
                                             LOAD_CONST YIELD_FROM

                    get_aiter            ::= expr GET_AITER

                    list_afor            ::= get_aiter list_afor2

                    return_expr_lambda   ::= list_comp_async


                    list_afor2           ::= async_iter store list_iter
                                             JUMP_LOOP COME_FROM_EXCEPT
                                             END_ASYNC_FOR

                    list_iter            ::= list_afor


                    set_afor             ::= get_aiter set_afor2
                    set_iter             ::= set_afor

                    set_comp_async       ::= BUILD_SET_0 LOAD_ARG
                                             set_comp_async

                   """,
                    nop_func,
                )
                custom_ops_processed.add(opname)

            elif opname == "GET_ANEXT":
                self.addRule(
                    """
                    expr                 ::= genexpr_func_async
                    expr                 ::= BUILD_MAP_0 genexpr_func_async
                    expr                 ::= list_comp_async

                    dict_comp_async      ::= BUILD_MAP_0 genexpr_func_async

                    async_iter           ::= _come_froms
                                              SETUP_EXCEPT
                                              GET_ANEXT
                                              LOAD_CONST
                                              YIELD_FROM
                                              POP_BLOCK

                    func_async_prefix    ::= _come_froms SETUP_EXCEPT GET_ANEXT
                                              LOAD_CONST YIELD_FROM

                    genexpr_func_async   ::= LOAD_ARG async_iter
                                             store
                                             comp_iter
                                             JUMP_LOOP
                                             COME_FROM_EXCEPT
                                             END_ASYNC_FOR

                    genexpr_func_async   ::= LOAD_ARG func_async_prefix
                                             store func_async_middle comp_iter
                                             JUMP_LOOP COME_FROM
                                             POP_TOP POP_TOP POP_TOP POP_EXCEPT POP_TOP

                    list_comp_async      ::= LOAD_ARG BUILD_LIST_FROM_ARG list_afor2
                    list_comp_async      ::= BUILD_LIST_0 LOAD_ARG list_afor2

                    set_afor2            ::= async_iter
                                             store
                                             set_iter
                                             JUMP_LOOP
                                             COME_FROM_FINALLY
                                             END_ASYNC_FOR

                    set_afor2            ::= expr_or_arg
                                             set_iter_async

                    set_comp_async       ::= BUILD_SET_0 set_afor2

                    set_iter_async       ::= async_iter
                                             store
                                             set_iter
                                             JUMP_LOOP
                                             _come_froms
                                             END_ASYNC_FOR

                    return_expr_lambda   ::= genexpr_func_async
                                             LOAD_CONST RETURN_VALUE
                                             RETURN_VALUE_LAMBDA

                    return_expr_lambda   ::= BUILD_SET_0 genexpr_func_async
                                             RETURN_VALUE_LAMBDA
                   """,
                    nop_func,
                )
                custom_ops_processed.add(opname)

            elif opname == "GET_AWAITABLE":
                rule_str = """
                    await      ::= GET_AWAITABLE LOAD_CONST YIELD_FROM
                    await_expr ::= expr await
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

            elif opname == "LOAD_CLOSURE":
                self.addRule("""load_closure ::= LOAD_CLOSURE+""", nop_func)

            elif opname == "LOAD_DICTCOMP":
                if has_get_iter_call_function1:
                    rule_pat = "dict_comp ::= LOAD_DICTCOMP %sMAKE_FUNCTION_0 get_iter CALL_FUNCTION_1"
                    self.add_make_function_rule(rule_pat, opname, token.attr, customize)
                    pass
                custom_ops_processed.add(opname)

            elif opname == "LOAD_GENEXPR":
                self.addRule("load_genexpr ::= LOAD_GENEXPR", nop_func)
                custom_ops_processed.add(opname)

            elif opname == "LOAD_LISTCOMP":
                self.add_unique_rule(
                    "expr ::= list_comp", opname, token.attr, customize
                )
                custom_ops_processed.add(opname)

            elif opname == "LOAD_NAME":
                if (
                    token.attr == "__annotations__"
                    and "SETUP_ANNOTATIONS" in self.seen_ops
                ):
                    token.kind = "LOAD_ANNOTATION"
                    self.addRule(
                        """
                        stmt       ::= SETUP_ANNOTATIONS
                        stmt       ::= ann_assign
                        ann_assign ::= expr LOAD_ANNOTATION LOAD_STR STORE_SUBSCR
                        """,
                        nop_func,
                    )
                    pass
            elif opname == "LOAD_SETCOMP":
                # Should this be generalized and put under MAKE_FUNCTION?
                if has_get_iter_call_function1:
                    self.addRule("expr ::= set_comp", nop_func)
                    rule_pat = "set_comp ::= LOAD_SETCOMP %sMAKE_FUNCTION_0 get_iter CALL_FUNCTION_1"
                    self.add_make_function_rule(rule_pat, opname, token.attr, customize)
                    pass
                custom_ops_processed.add(opname)
            elif opname == "LOOKUP_METHOD":
                # A PyPy speciality - DRY with parse3
                self.addRule(
                    """
                             expr      ::= attribute
                             attribute ::= expr LOOKUP_METHOD
                             """,
                    nop_func,
                )
                custom_ops_processed.add(opname)

            elif opname == "MAKE_FUNCTION_CLOSURE":
                if "LOAD_DICTCOMP" in self.seen_ops:
                    # Is there something general going on here?
                    rule = """
                       dict_comp ::= load_closure LOAD_DICTCOMP LOAD_STR
                                     MAKE_FUNCTION_CLOSURE expr
                                     GET_ITER CALL_FUNCTION_1
                       """
                    self.addRule(rule, nop_func)
                elif "LOAD_SETCOMP" in self.seen_ops:
                    rule = """
                       set_comp ::= load_closure LOAD_SETCOMP LOAD_STR
                                    MAKE_FUNCTION_CLOSURE expr
                                    GET_ITER CALL_FUNCTION_1
                       """
                    self.addRule(rule, nop_func)

            elif opname == "MAKE_FUNCTION_CLOSURE_POS":

                args_pos, args_kw, annotate_args, closure = token.attr
                stack_count = args_pos + args_kw + annotate_args

                if closure:

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
                        #                12  MAKE_FUNCTION_CLOSURE_POS   'default, closure'
                        # FIXME: Possibly we need to generalize for more nested lambda's of lambda's?
                        rule = """
                             expr        ::= lambda_body
                             lambda_body ::= %s%s%s%s
                             """ % (
                            "expr " * stack_count,
                            "load_closure " * closure,
                            "BUILD_TUPLE_2 LOAD_LAMBDA LOAD_STR ",
                            opname,
                        )
                        self.add_unique_rule(rule, opname, token.attr, customize)
                        rule = """
                             expr        ::= lambda_body
                             lambda_body ::= %s%s%s%s
                             """ % (
                            "expr " * stack_count,
                            "load_closure " * closure,
                            "LOAD_LAMBDA LOAD_STR ",
                            opname,
                        )

                    else:
                        rule = """
                             expr        ::= lambda_body
                             lambda_body ::= %s%s%s""" % (
                            "load_closure " * closure,
                            "LOAD_LAMBDA LOAD_STR ",
                            opname,
                        )
                    self.add_unique_rule(rule, opname, token.attr, customize)

            elif opname == "SETUP_WITH":
                rules_str = """
                with       ::= expr SETUP_WITH POP_TOP suite_stmts_opt COME_FROM_WITH
                               WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY

                # Removes POP_BLOCK LOAD_CONST from 3.6-
                with_as ::= expr SETUP_WITH store suite_stmts_opt COME_FROM_WITH
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
            rule_str = """
                await      ::= GET_AWAITABLE LOAD_CONST YIELD_FROM
                await_expr ::= expr await
                expr       ::= await_expr
            """
            self.add_unique_doc_rules(rule_str, customize)
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
