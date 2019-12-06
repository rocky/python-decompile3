#  Copyright (c) 2016-2017, 2019 Rocky Bernstein
"""
Skeletal code for Python 3.6 which is going to go away in decompyle6
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
            # FIXME: I suspect this is wrong for 3.6 and 3.5, but
            # I haven't verified what the 3.7ish fix is
            if opname == "BUILD_MAP_UNPACK_WITH_CALL":
                if self.version < 3.7:
                    self.addRule("expr ::= unmapexpr", nop_func)
                    nargs = token.attr % 256
                    map_unpack_n = "map_unpack_%s" % nargs
                    rule = map_unpack_n + " ::= " + "expr " * (nargs)
                    self.addRule(rule, nop_func)
                    rule = "unmapexpr ::=  %s %s" % (map_unpack_n, opname)
                    self.addRule(rule, nop_func)
                    call_token = tokens[i + 1]
                    rule = "call ::= expr unmapexpr " + call_token.kind
                    self.addRule(rule, nop_func)
            elif opname == "BEFORE_ASYNC_WITH" and self.version < 3.8:
                # Some Python 3.5+ async additions
                rules_str = """
                   async_with_stmt ::= expr
                   stmt ::= async_with_stmt

                   async_with_stmt ::= expr
                            BEFORE_ASYNC_WITH GET_AWAITABLE LOAD_CONST YIELD_FROM
                            SETUP_ASYNC_WITH POP_TOP suite_stmts_opt
                            POP_BLOCK LOAD_CONST COME_FROM_ASYNC_WITH
                            WITH_CLEANUP_START
                            GET_AWAITABLE LOAD_CONST YIELD_FROM
                            WITH_CLEANUP_FINISH END_FINALLY

                   stmt ::= async_with_as_stmt

                   async_with_as_stmt ::= expr
                               BEFORE_ASYNC_WITH GET_AWAITABLE LOAD_CONST YIELD_FROM
                               SETUP_ASYNC_WITH store suite_stmts_opt
                               POP_BLOCK LOAD_CONST COME_FROM_ASYNC_WITH
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

            elif opname == "SETUP_WITH":
                # Python 3.5+ has WITH_CLEANUP_START/FINISH
                rules_str = """
                  withstmt   ::= expr
                       SETUP_WITH POP_TOP suite_stmts_opt
                       POP_BLOCK LOAD_CONST COME_FROM_WITH
                       WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY

                  withasstmt ::= expr
                       SETUP_WITH store suite_stmts_opt
                       POP_BLOCK LOAD_CONST COME_FROM_WITH
                       WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY
                """
                self.addRule(rules_str, nop_func)
            pass
        return

    def custom_classfunc_rule(self, opname, token, customize, *args):
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
