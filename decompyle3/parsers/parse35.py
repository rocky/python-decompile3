#  Copyright (c) 2016-2017, 2019 Rocky Bernstein
"""
Skeletal code for Python 3.5 which is going to go away in decompyle6
"""
from decompyle3.parser import PythonParserSingle, nop_func
from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from decompyle3.parsers.parse3 import Python3Parser


class Python35Parser(Python3Parser):
    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python35Parser, self).__init__(debug_parser)
        self.customized = {}

    def customize_grammar_rules(self, tokens, customize):
        super(Python35Parser, self).customize_grammar_rules(tokens, customize)
        for i, token in enumerate(tokens):
            opname = token.kind

            if opname == "LOAD_ASSERT" and "PyPy" in customize:
                rules_str = """
                stmt ::= JUMP_IF_NOT_DEBUG stmts COME_FROM
                """
                self.add_unique_doc_rules(rules_str, customize)

            elif opname == "BEFORE_ASYNC_WITH":
                rules_str = """
                   stmt            ::= async_with_stmt
                   stmt            ::= async_with_as_stmt
                """

                if self.version < 3.8:
                    rules_str += """
                       async_with_stmt    ::= expr
                                              BEFORE_ASYNC_WITH GET_AWAITABLE LOAD_CONST YIELD_FROM
                                              SETUP_ASYNC_WITH POP_TOP suite_stmts_opt
                                              POP_BLOCK LOAD_CONST COME_FROM_ASYNC_WITH
                                              WITH_CLEANUP_START
                                              GET_AWAITABLE LOAD_CONST YIELD_FROM
                                              WITH_CLEANUP_FINISH END_FINALLY
                       async_with_as_stmt ::= expr
                                              BEFORE_ASYNC_WITH GET_AWAITABLE LOAD_CONST YIELD_FROM
                                              SETUP_ASYNC_WITH store suite_stmts_opt
                                              POP_BLOCK LOAD_CONST COME_FROM_ASYNC_WITH
                                              WITH_CLEANUP_START
                                              GET_AWAITABLE LOAD_CONST YIELD_FROM
                                              WITH_CLEANUP_FINISH END_FINALLY
                    """
                else:
                    rules_str += """
                       async_with_stmt    ::= expr
                                              BEFORE_ASYNC_WITH GET_AWAITABLE LOAD_CONST YIELD_FROM
                                              SETUP_ASYNC_WITH POP_TOP suite_stmts
                                              POP_TOP POP_BLOCK BEGIN_FINALLY COME_FROM_ASYNC_WITH
                                              WITH_CLEANUP_START
                                              GET_AWAITABLE LOAD_CONST YIELD_FROM
                                              WITH_CLEANUP_FINISH END_FINALLY
                       async_with_as_stmt ::= expr
                                              BEFORE_ASYNC_WITH GET_AWAITABLE LOAD_CONST YIELD_FROM
                                              SETUP_ASYNC_WITH store suite_stmts
                                              POP_TOP POP_BLOCK BEGIN_FINALLY COME_FROM_ASYNC_WITH
                                              WITH_CLEANUP_START
                                              GET_AWAITABLE LOAD_CONST YIELD_FROM
                                              WITH_CLEANUP_FINISH END_FINALLY
                    """
                self.addRule(rules_str, nop_func)

            elif opname == "BUILD_MAP_UNPACK":
                self.addRule(
                    """
                   expr       ::= unmap_dict
                   unmap_dict ::= dict_comp BUILD_MAP_UNPACK
                   """,
                    nop_func,
                )

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

            elif opname == "SETUP_WITH":
                rules_str = """
                  stmt       ::= withstmt
                  stmt       ::= withasstmt

                  withstmt   ::= expr SETUP_WITH POP_TOP suite_stmts_opt COME_FROM_WITH
                                 WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY
                  withasstmt ::= expr SETUP_WITH store suite_stmts_opt COME_FROM_WITH
                                 WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY

                  withstmt   ::= expr
                                 SETUP_WITH POP_TOP suite_stmts_opt
                                 POP_BLOCK LOAD_CONST COME_FROM_WITH
                                 WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY
                  withasstmt ::= expr
                                 SETUP_WITH store suite_stmts_opt
                                 POP_BLOCK LOAD_CONST COME_FROM_WITH
                                 WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY

                  withstmt   ::= expr
                                 SETUP_WITH POP_TOP suite_stmts_opt
                                 POP_BLOCK LOAD_CONST COME_FROM_WITH
                                 WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY
                  withasstmt ::= expr
                                 SETUP_WITH store suite_stmts_opt
                                 POP_BLOCK LOAD_CONST COME_FROM_WITH
                                 WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY
                """
                if self.version < 3.8:
                    rules_str += """
                    withstmt   ::= expr SETUP_WITH POP_TOP suite_stmts_opt POP_BLOCK
                                   LOAD_CONST
                                   WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY
                    """
                else:
                    rules_str += """
                      withstmt   ::= expr
                                     SETUP_WITH POP_TOP suite_stmts_opt
                                     POP_BLOCK LOAD_CONST COME_FROM_WITH
                                     WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY

                      withasstmt ::= expr
                                     SETUP_WITH store suite_stmts_opt
                                     POP_BLOCK LOAD_CONST COME_FROM_WITH

                       withstmt  ::= expr SETUP_WITH POP_TOP suite_stmts_opt POP_BLOCK
                                     BEGIN_FINALLY COME_FROM_WITH
                                     WITH_CLEANUP_START WITH_CLEANUP_FINISH
                                     END_FINALLY
                    """
                self.addRule(rules_str, nop_func)

            pass
        return

    def custom_classfunc_rule(self, opname, token, customize, *args):
        """
        call ::= expr {expr}^n CALL_FUNCTION_n
        call ::= expr {expr}^n CALL_FUNCTION_VAR_n
        call ::= expr {expr}^n CALL_FUNCTION_VAR_KW_n
        call ::= expr {expr}^n CALL_FUNCTION_KW_n

        classdefdeco2 ::= LOAD_BUILD_CLASS mkfunc {expr}^n-1 CALL_FUNCTION_n
        """
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
                + ("pos_arg " * args_pos)
                + ("kwarg " * args_kw)
                + "expr " * nak
                + token.kind
                + " GET_AWAITABLE LOAD_CONST YIELD_FROM"
            )
            self.add_unique_rule(rule, token.kind, uniq_param, customize)
            self.add_unique_rule(
                "expr ::= async_call", token.kind, uniq_param, customize
            )

        if opname.startswith("CALL_FUNCTION_VAR"):
            token.kind = self.call_fn_name(token)
            if opname.endswith("KW"):
                kw = "expr "
            else:
                kw = ""
            rule = (
                "call ::= expr expr "
                + ("pos_arg " * args_pos)
                + ("kwarg " * args_kw)
                + kw
                + token.kind
            )

            # Note: semantic actions make use of the fact of wheter  "args_pos"
            # zero or not in creating a template rule.
            self.add_unique_rule(rule, token.kind, args_pos, customize)
        else:
            super(Python35Parser, self).custom_classfunc_rule(
                opname, token, customize, *args
            )
