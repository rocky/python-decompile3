#  Copyright (c) 2016-2017, 2019 Rocky Bernstein
"""
spark grammar differences over Python 3 for Python 3.5.
"""
from decompyle3.parser import PythonParserSingle, nop_func
from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from decompyle3.parsers.parse3 import Python3Parser


class Python35Parser(Python3Parser):
    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python35Parser, self).__init__(debug_parser)
        self.customized = {}

    def p_35on(self, args):
        """

        # The number of canned instructions in new statements is mind boggling.
        # I'm sure by the time Python 4 comes around these will be turned
        # into special opcodes

        while1stmt     ::= setup_loop l_stmts COME_FROM JUMP_BACK
                           POP_BLOCK COME_FROM_LOOP
        while1stmt     ::= setup_loop l_stmts POP_BLOCK COME_FROM_LOOP
        while1elsestmt ::= setup_loop l_stmts JUMP_BACK
                           POP_BLOCK else_suite COME_FROM_LOOP

        # The following rule is for Python 3.5+ where we can have stuff like
        # while ..
        #     if
        #     ...
        # the end of the if will jump back to the loop and there will be a COME_FROM
        # after the jump
        l_stmts ::= lastl_stmt come_froms l_stmts

        # Python 3.5+ Await statement
        expr       ::= await_expr
        await_expr ::= expr GET_AWAITABLE LOAD_CONST YIELD_FROM

        stmt       ::= await_stmt
        await_stmt ::= await_expr POP_TOP

        # Python 3.5+ has WITH_CLEANUP_START/FINISH

        withstmt   ::= expr
                       SETUP_WITH POP_TOP suite_stmts_opt
                       POP_BLOCK LOAD_CONST COME_FROM_WITH
                       WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY

        withasstmt ::= expr
                       SETUP_WITH store suite_stmts_opt
                       POP_BLOCK LOAD_CONST COME_FROM_WITH
                       WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY

        # Python 3.5+ async additions

        inplace_op ::= INPLACE_MATRIX_MULTIPLY
        binary_op  ::= BINARY_MATRIX_MULTIPLY

        # Python 3.5+ does jump optimization
        # In <.3.5 the below is a JUMP_FORWARD to a JUMP_ABSOLUTE.

        return_if_stmt ::= ret_expr RETURN_END_IF POP_BLOCK
        return_if_lambda   ::= RETURN_END_IF_LAMBDA COME_FROM

        jb_else     ::= JUMP_BACK ELSE
        ifelsestmtc ::= testexpr c_stmts_opt JUMP_FORWARD else_suitec
        ifelsestmtl ::= testexpr c_stmts_opt jb_else else_suitel

        # 3.5 Has jump optimization which can route the end of an
        # "if/then" back to to a loop just before an else.
        jump_absolute_else ::= jb_else
        jump_absolute_else ::= CONTINUE ELSE

        # Our hacky "ELSE" determination doesn't do a good job and really
        # determine the start of an "else". It could also be the end of an
        # "if-then" which ends in a "continue". Perhaps with real control-flow
        # analysis we'll sort this out. Or call "ELSE" something more appropriate.
        _ifstmts_jump ::= c_stmts_opt ELSE

        # ifstmt ::= testexpr c_stmts_opt

        iflaststmt ::= testexpr c_stmts_opt JUMP_FORWARD
        """

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
            # Python 3.5 changes the stack position of *args. KW args come
            # after *args.

            # Note: Python 3.6+ replaces CALL_FUNCTION_VAR and
            # CALL_FUNCTION_VAR_KW with CALL_FUNCTION_EX

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


class Python35ParserSingle(Python35Parser, PythonParserSingle):
    pass


if __name__ == "__main__":
    # Check grammar
    p = Python35Parser()
    p.check_grammar()
