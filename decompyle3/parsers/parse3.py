#  Copyright (c) 2015-2019 Rocky Bernstein
#  Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
#  Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
#  Copyright (c) 1999 John Aycock
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
A spark grammar for Python 3.x.

However instead of terminal symbols being the usual ASCII text,
e.g. 5, myvariable, "for", etc.  they are CPython Bytecode tokens,
e.g. "LOAD_CONST 5", "STORE NAME myvariable", "SETUP_LOOP", etc.

If we succeed in creating a parse tree, then we have a Python program
that a later phase can turn into a sequence of ASCII text.
"""

from decompyle3.scanners.tok import Token
from decompyle3.parser import PythonParser, PythonParserSingle, nop_func
from decompyle3.parsers.treenode import SyntaxTree
from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG


class Python3Parser(PythonParser):
    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        self.added_rules = set()
        super(Python3Parser, self).__init__(SyntaxTree, "stmts", debug=debug_parser)
        self.new_rules = set()

    def customize_grammar_rules(self, tokens, customize):
        """The base grammar we start out for a Python version even with the
        subclassing is, well, is pretty base.  And we want it that way: lean and
        mean so that parsing will go faster.

        Here, we add additional grammar rules based on specific instructions
        that are in the instruction/token stream. In classes that
        inherit from from here and other versions, grammar rules may
        also be removed.

        For example if we see a pretty rare DELETE_DEREF instruction we'll
        add the grammar for that.

        More importantly, here we add grammar rules for instructions
        that may access a variable number of stack items. CALL_FUNCTION,
        BUILD_LIST and so on are like this.

        Without custom rules, there can be an super-exponential number of
        derivations. See the deparsing paper for an elaboration of
        this.

        """

        is_pypy = False

        # For a rough break out on the first word. This may
        # include instructions that don't need customization,
        # but we'll do a finer check after the rough breakout.
        customize_instruction_basenames = frozenset(
            (
                "BUILD",
                "CALL",
                "CONTINUE",
                "DELETE",
                "GET",
                "JUMP",
                "LOAD",
                "LOOKUP",
                "MAKE",
                "RETURN",
                "RAISE",
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

        # A set of instruction operation names that exist in the token stream.
        # We use this customize the grammar that we create.
        # 2.6-compatible set comprehensions
        self.seen_ops = frozenset([t.kind for t in tokens])
        self.seen_op_basenames = frozenset(
            [opname[: opname.rfind("_")] for opname in self.seen_ops]
        )

        # Loop over instructions adding custom grammar rules based on
        # a specific instruction seen.

        if "PyPy" in customize:
            is_pypy = True
            self.addRule(
                """
              stmt ::= assign3_pypy
              stmt ::= assign2_pypy
              assign3_pypy       ::= expr expr expr store store store
              assign2_pypy       ::= expr expr store store
              stmt               ::= if_expr_lambda
              stmt               ::= conditional_not_lambda
              if_expr_lambda     ::= expr jmp_false expr return_if_lambda
                                     return_lambda LAMBDA_MARKER
              conditional_not_lambda
                                 ::= expr jmp_true expr return_if_lambda
                                     return_lambda LAMBDA_MARKER
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
            # The order of opname listed is roughly sorted below
            if opname_base == "BUILD_CONST_KEY_MAP":
                # This is in 3.6+
                kvlist_n = "expr " * (token.attr)
                rule = "dict ::= %sLOAD_CONST %s" % (kvlist_n, opname)
                self.addRule(rule, nop_func)
            elif opname.startswith("BUILD_LIST_UNPACK"):
                v = token.attr
                rule = "build_list_unpack ::= %s%s" % ("expr " * v, opname)
                self.addRule(rule, nop_func)
                rule = "expr ::= build_list_unpack"
                self.addRule(rule, nop_func)
            elif opname_base in ("BUILD_MAP", "BUILD_MAP_UNPACK"):
                kvlist_n = "kvlist_%s" % token.attr
                if opname == "BUILD_MAP_n":
                    # PyPy sometimes has no count. Sigh.
                    rule = (
                        "dict_comp_func ::= BUILD_MAP_n LOAD_FAST for_iter store "
                        "comp_iter JUMP_BACK RETURN_VALUE RETURN_LAST"
                    )
                    self.add_unique_rule(rule, "dict_comp_func", 1, customize)

                    kvlist_n = "kvlist_n"
                    rule = "kvlist_n ::=  kvlist_n kv3"
                    self.add_unique_rule(rule, "kvlist_n", 0, customize)
                    rule = "kvlist_n ::="
                    self.add_unique_rule(rule, "kvlist_n", 1, customize)
                    rule = "dict ::=  BUILD_MAP_n kvlist_n"

                if not opname.startswith("BUILD_MAP_WITH_CALL"):
                    # FIXME: Use the attr
                    # so this doesn't run into exponential parsing time.
                    if opname.startswith("BUILD_MAP_UNPACK"):
                        # FIXME: start here. The LHS should be unmap_dict, not dict.
                        # FIXME: really we need a combination of dict_entry-like things.
                        # It just so happens the most common case is not to mix
                        # dictionary comphensions with dictionary, elements
                        if "LOAD_DICTCOMP" in self.seen_ops:
                            rule = "dict ::= %s%s" % ("dict_comp " * token.attr, opname)
                            self.addRule(rule, nop_func)
                        rule = """
                         expr       ::= unmap_dict
                         unmap_dict ::= %s%s
                         """ % (
                            "expr " * token.attr,
                            opname,
                        )
                    else:
                        rule = "%s ::= %s %s" % (
                            kvlist_n,
                            "expr " * (token.attr * 2),
                            opname,
                        )
                        self.add_unique_rule(rule, opname, token.attr, customize)
                        rule = "dict ::=  %s" % kvlist_n
                self.add_unique_rule(rule, opname, token.attr, customize)
            elif opname.startswith("BUILD_MAP_UNPACK_WITH_CALL"):
                v = token.attr
                rule = "build_map_unpack_with_call ::= %s%s" % ("expr " * v, opname)
                self.addRule(rule, nop_func)
            elif opname.startswith("BUILD_TUPLE_UNPACK_WITH_CALL"):
                v = token.attr
                rule = "starred ::= %s %s" % ("expr " * v, opname)
                self.addRule(rule, nop_func)

            elif opname_base in (
                "BUILD_LIST",
                "BUILD_SET",
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
            elif opname_base == "BUILD_SLICE":
                if token.attr == 2:
                    self.add_unique_rules(
                        [
                            "expr ::= build_slice2",
                            "build_slice2 ::= expr expr BUILD_SLICE_2",
                        ],
                        customize,
                    )
                else:
                    assert token.attr == 3, (
                        "BUILD_SLICE value must be 2 or 3; is %s" % v
                    )
                    self.add_unique_rules(
                        [
                            "expr ::= build_slice3",
                            "build_slice3 ::= expr expr expr BUILD_SLICE_3",
                        ],
                        customize,
                    )
            elif opname in frozenset(
                (
                    "CALL_FUNCTION",
                    "CALL_FUNCTION_EX",
                    "CALL_FUNCTION_EX_KW",
                    "CALL_FUNCTION_VAR",
                    "CALL_FUNCTION_VAR_KW",
                )
            ) or opname.startswith("CALL_FUNCTION_KW"):

                if opname == "CALL_FUNCTION" and token.attr == 1:
                    rule = """
                     dict_comp    ::= LOAD_DICTCOMP LOAD_STR MAKE_FUNCTION_0 expr
                                      GET_ITER CALL_FUNCTION_1
                    classdefdeco1 ::= expr classdefdeco2 CALL_FUNCTION_1
                    """
                    self.addRule(rule, nop_func)

                self.custom_classfunc_rule(opname, token, customize, tokens[i + 1])
                # Note: don't add to custom_ops_processed.

            elif opname_base == "CALL_METHOD":
                # PyPy and Python 3.7+ only - DRY with parse2

                args_pos, args_kw = self.get_pos_kw(token)

                # number of apply equiv arguments:
                nak = (len(opname_base) - len("CALL_METHOD")) // 3
                rule = (
                    "call ::= expr "
                    + ("pos_arg " * args_pos)
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
                self.addRule("del_stmt ::= expr DELETE_ATTR", nop_func)
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
                    del_stmt ::= delete_subscript
                    delete_subscript ::= expr expr DELETE_SUBSCR
                   """,
                    nop_func,
                )
                custom_ops_processed.add(opname)
            elif opname == "GET_ITER":
                self.addRule(
                    """
                    expr      ::= get_iter
                    attribute ::= expr GET_ITER
                    """,
                    nop_func,
                )
                custom_ops_processed.add(opname)
            elif opname == "JUMP_IF_NOT_DEBUG":
                v = token.attr
                self.addRule(
                    """
                    stmt        ::= assert_pypy
                    stmt        ::= assert2_pypy", nop_func)
                    assert_pypy ::=  JUMP_IF_NOT_DEBUG assert_expr jmp_true
                                     LOAD_ASSERT RAISE_VARARGS_1 COME_FROM
                    assert2_pypy ::= JUMP_IF_NOT_DEBUG assert_expr jmp_true
                                     LOAD_ASSERT expr CALL_FUNCTION_1
                                     RAISE_VARARGS_1 COME_FROM
                    assert2_pypy ::= JUMP_IF_NOT_DEBUG assert_expr jmp_true
                                     LOAD_ASSERT expr CALL_FUNCTION_1
                                     RAISE_VARARGS_1 COME_FROM,
                    """,
                    nop_func,
                )
                custom_ops_processed.add(opname)
            elif opname == "LOAD_BUILD_CLASS":
                self.custom_build_class_rule(opname, i, token, tokens, customize)
                # Note: don't add to custom_ops_processed.
            elif opname == "LOAD_CLASSDEREF":
                # Python 3.4+
                self.addRule("expr ::= LOAD_CLASSDEREF", nop_func)
                custom_ops_processed.add(opname)
            elif opname == "LOAD_CLASSNAME":
                self.addRule("expr ::= LOAD_CLASSNAME", nop_func)
                custom_ops_processed.add(opname)
            elif opname == "LOAD_DICTCOMP":
                if has_get_iter_call_function1:
                    rule_pat = (
                        "dict_comp ::= LOAD_DICTCOMP %sMAKE_FUNCTION_0 expr "
                        "GET_ITER CALL_FUNCTION_1"
                    )
                    self.add_make_function_rule(rule_pat, opname, token.attr, customize)
                    pass
                custom_ops_processed.add(opname)
            elif opname == "LOAD_ATTR":
                self.addRule(
                    """
                  expr      ::= attribute
                  attribute ::= expr LOAD_ATTR
                  """,
                    nop_func,
                )
                custom_ops_processed.add(opname)
            elif opname == "LOAD_LISTCOMP":
                self.add_unique_rule("expr ::= listcomp", opname, token.attr, customize)
                custom_ops_processed.add(opname)
            elif opname == "LOAD_SETCOMP":
                # Should this be generalized and put under MAKE_FUNCTION?
                if has_get_iter_call_function1:
                    self.addRule("expr ::= set_comp", nop_func)
                    rule_pat = (
                        "set_comp ::= LOAD_SETCOMP %sMAKE_FUNCTION_0 expr "
                        "GET_ITER CALL_FUNCTION_1"
                    )
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
            elif opname.startswith("MAKE_CLOSURE"):
                # DRY with MAKE_FUNCTION
                # Note: this probably doesn't handle kwargs proprerly

                if opname == "MAKE_CLOSURE_0" and "LOAD_DICTCOMP" in self.seen_ops:
                    # Is there something general going on here?
                    # Note that 3.6+ doesn't do this, but we'll remove
                    # this rule in parse36.py
                    rule = """
                        dict_comp ::= load_closure LOAD_DICTCOMP LOAD_STR
                                      MAKE_CLOSURE_0 expr
                                      GET_ITER CALL_FUNCTION_1
                    """
                    self.addRule(rule, nop_func)

                args_pos, args_kw, annotate_args = token.attr

                # FIXME: Fold test  into add_make_function_rule
                j = 2
                if is_pypy or (i >= j and tokens[i - j] == "LOAD_LAMBDA"):
                    rule_pat = "mklambda ::= %sload_closure LOAD_LAMBDA %%s%s" % (
                        "pos_arg " * args_pos,
                        opname,
                    )
                    self.add_make_function_rule(rule_pat, opname, token.attr, customize)

                if has_get_iter_call_function1:
                    rule_pat = (
                        "generator_exp ::= %sload_closure load_genexpr %%s%s expr "
                        "GET_ITER CALL_FUNCTION_1" % ("pos_arg " * args_pos, opname)
                    )
                    self.add_make_function_rule(rule_pat, opname, token.attr, customize)

                    if has_get_iter_call_function1:
                        if is_pypy or (i >= j and tokens[i - j] == "LOAD_LISTCOMP"):
                            # In the tokens we saw:
                            #   LOAD_LISTCOMP LOAD_CONST MAKE_FUNCTION (>= 3.3) or
                            #   LOAD_LISTCOMP MAKE_FUNCTION (< 3.3) or
                            #   and have GET_ITER CALL_FUNCTION_1
                            # Todo: For Pypy we need to modify this slightly
                            rule_pat = (
                                "listcomp ::= %sload_closure LOAD_LISTCOMP %%s%s expr "
                                "GET_ITER CALL_FUNCTION_1"
                                % ("pos_arg " * args_pos, opname)
                            )
                            self.add_make_function_rule(
                                rule_pat, opname, token.attr, customize
                            )
                        if is_pypy or (i >= j and tokens[i - j] == "LOAD_SETCOMP"):
                            rule_pat = (
                                "set_comp ::= %sload_closure LOAD_SETCOMP %%s%s expr "
                                "GET_ITER CALL_FUNCTION_1"
                                % ("pos_arg " * args_pos, opname)
                            )
                            self.add_make_function_rule(
                                rule_pat, opname, token.attr, customize
                            )
                        if is_pypy or (i >= j and tokens[i - j] == "LOAD_DICTCOMP"):
                            self.add_unique_rule(
                                "dict_comp ::= %sload_closure LOAD_DICTCOMP %s "
                                "expr GET_ITER CALL_FUNCTION_1"
                                % ("pos_arg " * args_pos, opname),
                                opname,
                                token.attr,
                                customize,
                            )

                if args_kw > 0:
                    kwargs_str = "kwargs "
                else:
                    kwargs_str = ""

                rule = "mkfunc ::= %s%s%s load_closure LOAD_CODE LOAD_STR %s" % (
                    "expr " * args_pos,
                    kwargs_str,
                    "expr " * annotate_args,
                    opname,
                )

                self.add_unique_rule(rule, opname, token.attr, customize)

                if args_kw == 0:
                    rule = "mkfunc ::= %sload_closure load_genexpr %s" % (
                        "pos_arg " * args_pos,
                        opname,
                    )
                    self.add_unique_rule(rule, opname, token.attr, customize)

                pass
            elif opname_base.startswith("MAKE_FUNCTION"):
                args_pos, args_kw, annotate_args, closure = token.attr
                stack_count = args_pos + args_kw + annotate_args
                if closure:
                    if args_pos:
                        rule = "mklambda ::= %s%s%s%s" % (
                            "expr " * stack_count,
                            "load_closure " * closure,
                            "BUILD_TUPLE_1 LOAD_LAMBDA LOAD_STR ",
                            opname,
                        )
                    else:
                        rule = "mklambda ::= %s%s%s" % (
                            "load_closure " * closure,
                            "LOAD_LAMBDA LOAD_STR ",
                            opname,
                        )
                    self.add_unique_rule(rule, opname, token.attr, customize)

                else:
                    rule = "mklambda ::= %sLOAD_LAMBDA LOAD_STR %s" % (
                        ("expr " * stack_count),
                        opname,
                    )
                    self.add_unique_rule(rule, opname, token.attr, customize)

                rule = "mkfunc ::= %s%s%s%s" % (
                    "expr " * stack_count,
                    "load_closure " * closure,
                    "LOAD_CODE LOAD_STR ",
                    opname,
                )
                self.add_unique_rule(rule, opname, token.attr, customize)

                if has_get_iter_call_function1:
                    rule_pat = (
                        "generator_exp ::= %sload_genexpr %%s%s expr "
                        "GET_ITER CALL_FUNCTION_1" % ("pos_arg " * args_pos, opname)
                    )
                    self.add_make_function_rule(
                        rule_pat, opname, token.attr, customize
                    )
                    rule_pat = (
                        "generator_exp ::= %sload_closure load_genexpr %%s%s expr "
                        "GET_ITER CALL_FUNCTION_1" % ("pos_arg " * args_pos, opname)
                    )
                    self.add_make_function_rule(
                        rule_pat, opname, token.attr, customize
                    )
                    if is_pypy or (i >= 2 and tokens[i - 2] == "LOAD_LISTCOMP"):
                        # 3.6+ sometimes bundles all of the
                        # 'exprs' in the rule above into a
                        # tuple.
                        rule_pat = (
                            "listcomp ::= load_closure LOAD_LISTCOMP %%s%s "
                            "expr GET_ITER CALL_FUNCTION_1" % (opname,)
                        )
                        self.add_make_function_rule(
                            rule_pat, opname, token.attr, customize
                        )
                        rule_pat = (
                            "listcomp ::= %sLOAD_LISTCOMP %%s%s expr "
                            "GET_ITER CALL_FUNCTION_1"
                            % ("expr " * args_pos, opname)
                        )
                        self.add_make_function_rule(
                            rule_pat, opname, token.attr, customize
                        )

                if is_pypy or (i >= 2 and tokens[i - 2] == "LOAD_LAMBDA"):
                    rule_pat = "mklambda ::= %s%sLOAD_LAMBDA %%s%s" % (
                        ("pos_arg " * args_pos),
                        ("kwarg " * args_kw),
                        opname,
                    )
                    self.add_make_function_rule(
                        rule_pat, opname, token.attr, customize
                    )
                continue

                args_pos, args_kw, annotate_args, closure = token.attr

                j = 2

                if has_get_iter_call_function1:
                    rule_pat = (
                        "generator_exp ::= %sload_genexpr %%s%s expr "
                        "GET_ITER CALL_FUNCTION_1" % ("pos_arg " * args_pos, opname)
                    )
                    self.add_make_function_rule(rule_pat, opname, token.attr, customize)

                    if is_pypy or (i >= j and tokens[i - j] == "LOAD_LISTCOMP"):
                        # In the tokens we saw:
                        #   LOAD_LISTCOMP LOAD_CONST MAKE_FUNCTION (>= 3.3) or
                        #   LOAD_LISTCOMP MAKE_FUNCTION (< 3.3) or
                        #   and have GET_ITER CALL_FUNCTION_1
                        # Todo: For Pypy we need to modify this slightly
                        rule_pat = (
                            "listcomp ::= %sLOAD_LISTCOMP %%s%s expr "
                            "GET_ITER CALL_FUNCTION_1" % ("expr " * args_pos, opname)
                        )
                        self.add_make_function_rule(
                            rule_pat, opname, token.attr, customize
                        )

                # FIXME: Fold test  into add_make_function_rule
                if is_pypy or (i >= j and tokens[i - j] == "LOAD_LAMBDA"):
                    rule_pat = "mklambda ::= %s%sLOAD_LAMBDA %%s%s" % (
                        ("pos_arg " * args_pos),
                        ("kwarg " * args_kw),
                        opname,
                    )
                    self.add_make_function_rule(rule_pat, opname, token.attr, customize)

                if args_kw == 0:
                    kwargs = "no_kwargs"
                    self.add_unique_rule("no_kwargs ::=", opname, token.attr, customize)
                else:
                    kwargs = "kwargs"

                # positional args before keyword args
                rule = "mkfunc ::= %s%s %s%s" % (
                    "pos_arg " * args_pos,
                    kwargs,
                    "LOAD_CODE LOAD_STR ",
                    opname,
                )
                self.add_unique_rule(rule, opname, token.attr, customize)

            elif opname == "RETURN_VALUE_LAMBDA":
                self.addRule(
                    """
                    return_lambda ::= ret_expr RETURN_VALUE_LAMBDA
                    """,
                    nop_func,
                )
                custom_ops_processed.add(opname)
            elif opname == "RAISE_VARARGS_0":
                self.addRule(
                    """
                    stmt        ::= raise_stmt0
                    raise_stmt0 ::= RAISE_VARARGS_0
                    """,
                    nop_func,
                )
                custom_ops_processed.add(opname)
            elif opname == "RAISE_VARARGS_1":
                self.addRule(
                    """
                    stmt        ::= raise_stmt1
                    raise_stmt1 ::= expr RAISE_VARARGS_1
                    """,
                    nop_func,
                )
                custom_ops_processed.add(opname)
            elif opname == "RAISE_VARARGS_2":
                self.addRule(
                    """
                    stmt        ::= raise_stmt2
                    raise_stmt2 ::= expr expr RAISE_VARARGS_2
                    """,
                    nop_func,
                )
                custom_ops_processed.add(opname)
            elif opname == "SETUP_EXCEPT":
                self.addRule(
                    """
                    try_except     ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                                       except_handler opt_come_from_except

                    tryelsestmt    ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                                       except_handler else_suite come_from_except_clauses

                    tryelsestmt    ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                                       except_handler else_suite come_froms

                    tryelsestmtl   ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                                       except_handler else_suitel come_from_except_clauses

                    stmt             ::= tryelsestmtl3
                    tryelsestmtl3    ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                                         except_handler COME_FROM else_suitel
                                         opt_come_from_except
                    """,
                    nop_func,
                )
                custom_ops_processed.add(opname)
            elif opname_base in ("UNPACK_EX",):
                before_count, after_count = token.attr
                rule = (
                    "unpack ::= " + opname + " store" * (before_count + after_count + 1)
                )
                self.addRule(rule, nop_func)
            elif opname_base in ("UNPACK_TUPLE", "UNPACK_SEQUENCE"):
                rule = "unpack ::= " + opname + " store" * token.attr
                self.addRule(rule, nop_func)
            elif opname_base == "UNPACK_LIST":
                rule = "unpack_list ::= " + opname + " store" * token.attr
                self.addRule(rule, nop_func)
                custom_ops_processed.add(opname)
                pass
            pass
        return
