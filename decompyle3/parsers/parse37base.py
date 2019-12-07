#  Copyright (c) 2016-2017, 2019 Rocky Bernstein
"""
Python 3.7 base code. We keep non-custom-generated grammar rules out of this file.
"""
from decompyle3.scanners.tok import Token
from decompyle3.parser import PythonParserSingle, nop_func
from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from decompyle3.parsers.parse3 import Python3Parser


class Python37BaseParser(Python3Parser):
    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python37BaseParser, self).__init__(debug_parser)
        self.customized = {}

    @staticmethod
    def call_fn_name(token):
        """Customize CALL_FUNCTION to add the number of positional arguments"""
        if token.attr is not None:
            return "%s_%i" % (token.kind, token.attr)
        else:
            return "%s_0" % (token.kind)

    def add_make_function_rule(self, rule, opname, attr, customize):
        """Python 3.3 added a an addtional LOAD_STR before MAKE_FUNCTION and
        this has an effect on many rules.
        """
        new_rule = rule % "LOAD_STR "
        self.add_unique_rule(new_rule, opname, attr, customize)

    def custom_build_class_rule(self, opname, i, token, tokens, customize):
        """
        # Should the first rule be somehow folded into the 2nd one?
        build_class ::= LOAD_BUILD_CLASS mkfunc
                        LOAD_CLASSNAME {expr}^n-1 CALL_FUNCTION_n
                        LOAD_CONST CALL_FUNCTION_n
        build_class ::= LOAD_BUILD_CLASS mkfunc
                        expr
                        call
                        CALL_FUNCTION_3
         """
        # FIXME: I bet this can be simplified
        # look for next MAKE_FUNCTION
        for i in range(i + 1, len(tokens)):
            if tokens[i].kind.startswith("MAKE_FUNCTION"):
                break
            elif tokens[i].kind.startswith("MAKE_CLOSURE"):
                break
            pass
        assert i < len(
            tokens
        ), "build_class needs to find MAKE_FUNCTION or MAKE_CLOSURE"
        assert (
            tokens[i + 1].kind == "LOAD_STR"
        ), "build_class expecting CONST after MAKE_FUNCTION/MAKE_CLOSURE"
        call_fn_tok = None
        for i in range(i, len(tokens)):
            if tokens[i].kind.startswith("CALL_FUNCTION"):
                call_fn_tok = tokens[i]
                break
        if not call_fn_tok:
            raise RuntimeError(
                "build_class custom rule for %s needs to find CALL_FUNCTION" % opname
            )

        # customize build_class rule
        # FIXME: What's the deal with the two rules? Different Python versions?
        # Different situations? Note that the above rule is based on the CALL_FUNCTION
        # token found, while this one doesn't.
        # 3.6+ handling
        call_function = call_fn_tok.kind
        if call_function.startswith("CALL_FUNCTION_KW"):
            self.addRule("classdef ::= build_class_kw store", nop_func)
            rule = "build_class_kw ::= LOAD_BUILD_CLASS mkfunc %sLOAD_CONST %s" % (
                "expr " * (call_fn_tok.attr - 1),
                call_function,
            )
        else:
            call_function = self.call_fn_name(call_fn_tok)
            rule = "build_class ::= LOAD_BUILD_CLASS mkfunc %s%s" % (
                "expr " * (call_fn_tok.attr - 1),
                call_function,
            )
        self.addRule(rule, nop_func)
        return

    def customize_grammar_rules(self, tokens, customize):
        super(Python37BaseParser, self).customize_grammar_rules(tokens, customize)
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

        self.check_reduce["and"] = "AST"
        self.check_reduce["aug_assign1"] = "AST"
        self.check_reduce["aug_assign2"] = "AST"
        self.check_reduce["while1stmt"] = "noAST"
        self.check_reduce["while1elsestmt"] = "noAST"
        self.check_reduce["_ifstmts_jump"] = "AST"
        self.check_reduce["ifelsestmt"] = "AST"
        self.check_reduce["iflaststmt"] = "AST"
        self.check_reduce["ifstmt"] = "AST"
        self.check_reduce["annotate_tuple"] = "noAST"

        # FIXME: remove parser errors caused by the below
        # self.check_reduce['while1elsestmt'] = 'noAST'

        return

    def custom_classfunc_rule(self, opname, token, customize, next_token):
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
            token.kind = self.call_fn_name(token)
            uniq_param = args_kw + args_pos

            # Note: 3.5+ have subclassed this method; so we don't handle
            # 'CALL_FUNCTION_VAR' or 'CALL_FUNCTION_EX' here.
            rule = (
                "call ::= expr "
                + ("pos_arg " * args_pos)
                + ("kwarg " * args_kw)
                + "expr " * nak
                + token.kind
            )

            self.add_unique_rule(rule, token.kind, uniq_param, customize)

            if "LOAD_BUILD_CLASS" in self.seen_ops:
                if next_token == "CALL_FUNCTION" and next_token.attr == 1 and args_pos > 1:
                    rule = "classdefdeco2 ::= LOAD_BUILD_CLASS mkfunc %s%s_%d" % (
                        ("expr " * (args_pos - 1)),
                        opname,
                        args_pos,
                    )
                    self.add_unique_rule(rule, token.kind, uniq_param, customize)

    def reduce_is_invalid(self, rule, ast, tokens, first, last):
        lhs = rule[0]

        if lhs == "and" and ast:
            # FIXME: put in a routine somewhere
            # Compare with parse30.py of uncompyle6
            jmp = ast[1]
            if jmp.kind.startswith("jmp_"):
                if last == len(tokens):
                    return True
                jmp_target = jmp[0].attr
                jmp_offset = jmp[0].offset

                if tokens[first].off2int() <= jmp_target < tokens[last].off2int():
                    return True
                if rule == ("and", ("expr", "jmp_false", "expr", "jmp_false")):
                    jmp2_target = ast[3][0].attr
                    return jmp_target != jmp2_target
                elif rule == ("and", ("expr", "jmp_false", "expr")):
                    if tokens[last] == "POP_JUMP_IF_FALSE":
                        return jmp_target != tokens[last].attr
                elif rule == ("and", ("expr", "jmp_false", "expr", "COME_FROM")):
                    return ast[-1].attr != jmp_offset
                # elif rule == ("and", ("expr", "jmp_false", "expr", "COME_FROM")):
                #     return jmp_offset != tokens[first+3].attr

                return jmp_target != tokens[last].off2int()
            return False

        elif lhs in ("aug_assign1", "aug_assign2") and ast[0][0] == "and":
            return True
        elif lhs == "annotate_tuple":
            return not isinstance(tokens[first].attr, tuple)
        elif lhs == "while1elsestmt":

            n = len(tokens)
            if last == n:
                # Adjust for fuzziness in parsing
                last -= 1

            if tokens[last] == "COME_FROM_LOOP":
                last -= 1
            elif tokens[last - 1] == "COME_FROM_LOOP":
                last -= 2
            if tokens[last] in ("JUMP_BACK", "CONTINUE"):
                # These indicate inside a loop, but token[last]
                # should not be in a loop.
                # FIXME: Not quite right: refine by using target
                return True

            # if SETUP_LOOP target spans the else part, then this is
            # not while1else. Also do for whileTrue?
            last += 1
            # 3.8+ Doesn't have SETUP_LOOP
            return self.version < 3.8 and tokens[first].attr > tokens[last].off2int()

        elif lhs == "while1stmt":

            # If there is a fall through to the COME_FROM_LOOP, then this is
            # not a while 1. So the instruction before should either be a
            # JUMP_BACK or the instruction before should not be the target of a
            # jump. (Well that last clause i not quite right; that target could be
            # from dead code. Ugh. We need a more uniform control flow analysis.)
            if last == len(tokens) or tokens[last - 1] == "COME_FROM_LOOP":
                cfl = last - 1
            else:
                cfl = last
            assert tokens[cfl] == "COME_FROM_LOOP"

            for i in range(cfl - 1, first, -1):
                if tokens[i] != "POP_BLOCK":
                    break
            if tokens[i].kind not in ("JUMP_BACK", "RETURN_VALUE"):
                if not tokens[i].kind.startswith("COME_FROM"):
                    return True

            # Check that the SETUP_LOOP jumps to the offset after the
            # COME_FROM_LOOP
            if 0 <= last < len(tokens) and tokens[last] in (
                "COME_FROM_LOOP",
                "JUMP_BACK",
            ):
                # jump_back should be right before COME_FROM_LOOP?
                last += 1
            if last == len(tokens):
                last -= 1
            offset = tokens[last].off2int()
            assert tokens[first] == "SETUP_LOOP"
            if offset != tokens[first].attr:
                return True
            return False
        elif lhs == "_ifstmts_jump" and len(rule[1]) > 1 and ast:
            come_froms = ast[-1]
            # Make sure all of the "come froms" offset at the
            # end of the "if" come from somewhere inside the "if".
            # Since the come_froms are ordered so that lowest
            # offset COME_FROM is last, it is sufficient to test
            # just the last one.

            # This is complicated, but note that the JUMP_IF instruction comes immediately
            # *before* _ifstmts_jump so that's what we have to test
            # the COME_FROM against. This can be complicated by intervening
            # POP_TOP, and pseudo COME_FROM, ELSE instructions
            #
            pop_jump_index = first - 1
            while pop_jump_index > 0 and tokens[pop_jump_index] in (
                "ELSE",
                "POP_TOP",
                "JUMP_FORWARD",
                "COME_FROM",
            ):
                pop_jump_index -= 1
            come_froms = ast[-1]

            # FIXME: something is fishy when and EXTENDED ARG is needed before the
            # pop_jump_index instruction to get the argment. In this case, the
            # _ifsmtst_jump can jump to a spot beyond the come_froms.
            # That is going on in the non-EXTENDED_ARG case is that the POP_JUMP_IF
            # jumps to a JUMP_(FORWARD) which is changed into an EXTENDED_ARG POP_JUMP_IF
            # to the jumped forwareded address
            if tokens[pop_jump_index].attr > 256:
                return False

            if isinstance(come_froms, Token):
                return (
                    come_froms.attr is not None
                    and tokens[pop_jump_index].offset > come_froms.attr
                )

            elif len(come_froms) == 0:
                return False
            else:
                return tokens[pop_jump_index].offset > come_froms[-1].attr

        elif lhs == "ifstmt" and ast:
            # FIXME: put in a routine somewhere
            testexpr = ast[0]

            # Compare with parse30.py of uncompyle6
            if testexpr[0] in ("testtrue", "testfalse"):
                test = testexpr[0]
                if len(test) > 1 and test[1].kind.startswith("jmp_"):
                    if last == len(tokens):
                        last -= 1
                    jmp_target = test[1][0].attr
                    if tokens[first].off2int() <= jmp_target < tokens[last].off2int():
                        return True
                    # jmp_target less than tokens[first] is okay - is to a loop
                    # jmp_target equal tokens[last] is also okay: normal non-optimized non-loop jump
                    if jmp_target > tokens[last].off2int():
                        # One more weird case to look out for
                        #   if c1:
                        #      if c2:  # Jumps around the *outer* "else"
                        #       ...
                        #   else:
                        if jmp_target == tokens[last - 1].attr:
                            return False
                        if last < len(tokens) and tokens[last].kind.startswith("JUMP"):
                            return False
                        return True

                pass
            return False
        elif lhs == "iflaststmt" and ast:
            # FIXME: put in a routine somewhere
            testexpr = ast[0]

            # Compare with parse30.py of uncompyle6
            if testexpr[0] in ("testtrue", "testfalse"):
                test = testexpr[0]
                if len(test) > 1 and test[1].kind.startswith("jmp_"):
                    if last == len(tokens):
                        last -= 1
                    jmp_target = test[1][0].attr
                    if tokens[first].off2int() <= jmp_target < tokens[last].off2int():
                        return True
                    # jmp_target less than tokens[first] is okay - is to a loop
                    # jmp_target equal tokens[last] is also okay: normal non-optimized non-loop jump

                    # If the instruction before "first" is a "POP_JUMP_IF_FALSE" which goes
                    # to the same target as jmp_target, then this not nested "if .. if .."
                    # but rather "if ... and ..."
                    if first > 0 and tokens[first - 1] == "POP_JUMP_IF_FALSE":
                        return tokens[first - 1].attr == jmp_target

                    if jmp_target > tokens[last].off2int():
                        # One more weird case to look out for
                        #   if c1:
                        #      if c2:  # Jumps around the *outer* "else"
                        #       ...
                        #   else:
                        if jmp_target == tokens[last - 1].attr:
                            return False
                        if last < len(tokens) and tokens[last].kind.startswith("JUMP"):
                            return False
                        return True

                pass
            return False
        elif rule in (
            (
                "ifelsestmt",
                (
                    "testexpr",
                    "c_stmts_opt",
                    "jump_forward_else",
                    "else_suite",
                    "_come_froms",
                ),
            ),
            (
                "ifelsestmt",
                (
                    "testexpr",
                    "c_stmts_opt",
                    "jf_cfs",
                    "else_suite",
                    "opt_come_from_except",
                ),
            ),
        ):
            # FIXME: put in a routine somewhere

            # Make sure all of the "come froms" offset at the
            # end of the "if" come from somewhere inside the "if".
            # Since the come_froms are ordered so that lowest
            # offset COME_FROM is last, it is sufficient to test
            # just the last one.
            come_froms = ast[-1]
            if come_froms == "opt_come_from_except" and len(come_froms) > 0:
                come_froms = come_froms[0]
            if not isinstance(come_froms, Token):
                return tokens[first].offset > come_froms[-1].attr
            elif tokens[first].offset > come_froms.attr:
                return True

            # For mysterious reasons a COME_FROM in tokens[last+1] might be part of the grammar rule
            # even though it is not found in come_froms.
            # Work around this.
            if (
                last < len(tokens)
                and tokens[last] == "COME_FROM"
                and tokens[first].offset > tokens[last].attr
            ):
                return True

            testexpr = ast[0]

            # Check that the condition portion of the "if"
            # jumps to the "else" part.
            # Compare with parse30.py of uncompyle6
            if testexpr[0] in ("testtrue", "testfalse"):
                test = testexpr[0]
                if len(test) > 1 and test[1].kind.startswith("jmp_"):
                    if last == len(tokens):
                        last -= 1
                    jmp = test[1]
                    jmp_target = jmp[0].attr
                    if tokens[first].off2int() > jmp_target:
                        return True
                    return (jmp_target > tokens[last].off2int()) and tokens[
                        last
                    ] != "JUMP_FORWARD"

            return False

        return False
