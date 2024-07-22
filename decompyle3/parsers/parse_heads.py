#  Copyright (c) 2022-2024 Rocky Bernstein
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
"""Here we have the top-level parse grammar types with their rules and the start symbols
for them.

Specific Python versions such as for Python 3.10 subclass these and
add in grammar rules that are custom to them.

However at the top-level they are all the same and share the same start symbol
and start-symbol grammar rule.

"""
# The below adds a special "start" rule for the kind of thing that we want to
# decompile

from typing import Union

from spark_parser import GenericASTBuilder

from decompyle3.parsers.treenode import SyntaxTree


def nop_func(self, args):
    return None


class ParserError(Exception):
    def __init__(self, token, offset: int, debug: bool):
        self.token = token
        self.offset = offset
        self.debug = debug

    def __str__(self) -> str:
        return "Parse error at or near `%r' instruction at offset %s\n" % (
            self.token,
            self.offset,
        )


class PythonBaseParser(GenericASTBuilder):
    def __init__(self, debug_parser, start_symbol, is_lambda=False):

        # Note: order of debug_parser, and start_symbol is reverse from above.
        # This is because (at least at one time), start_symbol can be defaulted
        # in the setup, while debug_parser could have been but wasn't.
        GenericASTBuilder.__init__(self, SyntaxTree, start_symbol, debug_parser)

        # FIXME: customize per python parser version

        # These are the non-terminals we should collect into a list.
        # For example instead of:
        #   stmts -> stmts stmt -> stmts stmt stmt ...
        # collect as stmts -> stmt stmt ...
        nt_list = [
            "and_parts",
            "attributes",
            "add_consts",
            "dicts_unmap",
            "doms_end",
            "exprs",
            "kvlist",
            "kwargs",
            "lists",
            "or_parts",
            "stmts",
        ]
        self.collect = frozenset(nt_list)

        # For these items we need to keep the 1st epslion reduction since
        # the nonterminal name is used in a semantic action.
        self.keep_epsilon = frozenset(("kvlist_n", "kvlist"))

        # ??? Do we need a debug option to skip eliding singleton reductions?
        # Time will tell if it if useful in debugging

        # FIXME: optional_nt is a misnomer. It's really about there being a
        # singleton reduction that we can simplify. It also happens to be optional
        # in its other derivation
        self.optional_nt |= frozenset(("suite_stmts", "c_stmts_opt", "stmt", "sstmt"))

        # Reduce singleton reductions in these nonterminals:
        # FIXME: would love to do sstmts, stmts and
        # so on but that would require major changes to the
        # semantic actions
        self.singleton = frozenset(("str", "store", "inplace_op"))
        # Instructions filled in from scanner
        self.insts = []

        # True if we are parsing inside a lambda expression.
        # because a lambda expression are written on a single line, certain line-oriented
        # statements behave differently
        self.is_lambda = is_lambda

        self.start_symbol = start_symbol
        self.new_rules = set()

        # Placeholder for Python version tuple
        self.version = (None, None)

    def ast_first_offset(self, ast) -> Union[int, str]:
        return ast.offset if hasattr(ast, "offset") else self.ast_first_offset(ast[0])

    def add_unique_rule(
        self, rule, opname: str, arg_count: int, customize: dict
    ) -> None:
        """Add rule to grammar, but only if it hasn't been added previously
        opname and stack_count are used in the customize() semantic
        the actions to add the semantic action rule. Stack_count is
        used in custom opcodes like MAKE_FUNCTION to indicate how
        many arguments it has. Often it is not used.
        """
        if rule not in self.new_rules:
            # print("XXX ", rule) # debug
            self.new_rules.add(rule)
            self.addRule(rule, nop_func)
            customize[opname] = arg_count
            pass
        return

    def add_unique_rules(self, rules: list, customize: dict) -> None:
        """Add rules (a list of string) to grammar. Note that
        the rules must not be those that set arg_count in the
        custom dictionary.
        """
        for rule in rules:
            if len(rule) == 0:
                continue
            opname = rule.split("::=")[0].strip()
            self.add_unique_rule(rule, opname, 0, customize)
        return

    def add_unique_doc_rules(self, rules_str: str, customize: dict) -> None:
        """Add rules (a docstring-like list of rules) to grammar.
        Note that the rules must not be those that set arg_count in the
        custom dictionary.
        """
        # print(rules_str)
        rules = [r.strip() for r in rules_str.split("\n")]
        self.add_unique_rules(rules, customize)
        return

    def cleanup(self):
        """
        Remove recursive references to allow garbage
        collector to collect this object.
        """
        for dict in (self.rule2func, self.rules, self.rule2name):
            for i in list(dict.keys()):
                dict[i] = None
        for i in dir(self):
            setattr(self, i, None)

    def debug_reduce(self, rule, tokens, parent, last_token_pos):
        """Customized format and print for our kind of tokens
        which gets called in debugging grammar reduce rules
        """

        def fix(c):
            s = str(c)
            last_token_pos = s.find("_")
            if last_token_pos == -1:
                return s
            else:
                return s[:last_token_pos]

        prefix = ""
        if parent and tokens:
            p_token = tokens[parent]
            if hasattr(p_token, "linestart") and p_token.linestart:
                prefix = "L.%3d: " % p_token.linestart
            else:
                prefix = "       "
            if hasattr(p_token, "offset"):
                prefix += "%3s" % fix(p_token.offset)
                if len(rule[1]) > 1:
                    prefix += "-%-3s " % fix(tokens[last_token_pos - 1].offset)
                else:
                    prefix += "     "
        else:
            prefix = "               "

        print("%s%s ::= %s (%d)" % (prefix, rule[0], " ".join(rule[1]), last_token_pos))

    def error(self, instructions, index):
        # Find the last line boundary
        start, finish = -1, -1
        for start in range(index, -1, -1):
            if instructions[start].linestart:
                break
            pass
        for finish in range(index + 1, len(instructions)):
            if instructions[finish].linestart:
                break
            pass
        if start >= 0:
            err_token = instructions[index]
            print("Instruction context:")
            for i in range(start, finish):
                if i != index:
                    indent = "   "
                else:
                    indent = "-> "
                print("%s%s" % (indent, instructions[i]))
            raise ParserError(err_token, err_token.offset, self.debug["reduce"])
        else:
            raise ParserError(None, -1, self.debug["reduce"])

    def get_pos_kw(self, token):
        """Return then the number of positional parameters and
        represented by the attr field of token"""
        # Low byte indicates number of positional parameters,
        # high byte number of keyword parameters
        args_pos = token.attr & 0xFF
        args_kw = (token.attr >> 8) & 0xFF
        return args_pos, args_kw

    def nonterminal(self, nt, args):
        n = len(args)

        # # Use this to find lots of singleton rule
        # if n == 1 and nt not in self.singleton:
        #     print("XXX", nt)

        if nt in self.collect and n > 1:
            #
            #  Collect iterated thingies together. That is rather than
            #  stmts -> stmts stmt -> stmts stmt -> ...
            #  stmms -> stmt stmt ...
            #
            if not hasattr(args[0], "append"):
                # Was in self.optional_nt as a single item, but we find we have
                # more than one now...
                rv = GenericASTBuilder.nonterminal(self, nt, [args[0]])
            else:
                rv = args[0]
                pass
            # In a  list-like entity where the first item goes to epsilon,
            # drop that and save the 2nd item as the first one
            if len(rv) == 0 and nt not in self.keep_epsilon:
                rv = args[1]
            else:
                rv.append(args[1])
        elif n == 1 and args[0] in self.singleton:
            rv = GenericASTBuilder.nonterminal(self, nt, args[0])
            del args[0]  # save memory
        elif n == 1 and nt in self.optional_nt:
            rv = args[0]
        else:
            rv = GenericASTBuilder.nonterminal(self, nt, args)
        return rv

    def off2inst(self, token):
        """
        Return the corresponding instruction for this token
        """
        offset = token.off2int(prefer_last=False)
        return self.insts[self.offset2inst_index[offset]]

    def __ambiguity(self, children):
        # only for debugging! to be removed hG/2000-10-15
        print(children)
        return GenericASTBuilder.ambiguity(self, children)

    def resolve(self, list):
        if len(list) == 2 and "function_def" in list and "assign" in list:
            return "function_def"
        if "grammar" in list and "expr" in list:
            return "expr"
        return GenericASTBuilder.resolve(self, list)


class PythonParserExpr(PythonBaseParser):
    """This corresponds to a single grammar expression: "expr". It matches smaller
    units, so it is something to parse for that might be used when larger
    pieces of code can't decompile.

    """

    def p_start_rule_expr(self, args):
        """
        expr_start       ::= expr return_value_opt
        return_value_opt ::= RETURN_VALUE?
        """

    def __init__(self, debug_parser, start_symbol="expr_start"):
        super(PythonParserExpr, self).__init__(
            debug_parser=debug_parser, start_symbol=start_symbol
        )


PythonParserEval = PythonParserExpr


class PythonParserExec(PythonBaseParser):
    """
    This corresponds to the compile-mode == "exec" of the `compile()` builtin
    or exec() builtin function
    """

    # def p_exec(self, args):
    #     """
    #     stmts ::= stmt+
    #     """

    def __init__(self, debug_parser, start_symbol="stmts"):
        super(PythonParserExec, self).__init__(
            debug_parser=debug_parser, start_symbol=start_symbol
        )


class PythonParserLambda(PythonBaseParser):
    """
    This corresponds to the Python lambda definitions
    """

    def p_start_rule_lambda(self, args):
        """
        lambda_start ::= return_expr_lambda
        """

    # lambda_start is the highest level nonterminal. However
    # we can pass in other nonterminals like "expr" for a different
    # parse.
    def __init__(self, debug_parser, start_symbol="lambda_start"):
        super(PythonParserLambda, self).__init__(
            start_symbol=start_symbol, debug_parser=debug_parser
        )


class PythonParserSingle(PythonBaseParser):
    def p_start_rule_single(self, args):
        """
        # Single-mode interactive compilation
        single_start ::= expr PRINT_EXPR
        single_start ::= stmt
        """

    def __init__(self, debug_parser, start_symbol="single_start"):
        super(PythonParserSingle, self).__init__(
            start_symbol=start_symbol, debug_parser=debug_parser
        )


class PythonParser(PythonBaseParser):
    def __init__(self, compile_mode, debug_parser):
        # FIXME: go over.
        if compile_mode == "single":
            PythonParserSingle.__init__(self, debug_parser=debug_parser)
        elif compile_mode == "lambda":
            PythonParserLambda.__init__(self, debug_parser=debug_parser)
        elif compile_mode == "eval":
            PythonParserEval.__init__(self, debug_parser=debug_parser)
        elif compile_mode == "exec":
            PythonParserExec.__init__(self, debug_parser=debug_parser)
        elif compile_mode == "eval_expr":
            PythonParserEval.__init__(self, debug_parser=debug_parser)

        else:
            raise BaseException(
                f'compile_mode should be either "exec", "single", "lambda", or "eval_expr"; got {compile_mode}'
            )

        # FIXME: customize per python parser version

        # These are the non-terminals we should collect into a list.
        # For example instead of:
        #   stmts -> stmts stmt -> stmts stmt stmt ...
        # collect as stmts -> stmt stmt ...
        nt_list = [
            "_stmts",
            "and_parts",
            "attributes",
            "except_stmts",
            "exprlist",
            "importlist",
            "kvlist",
            "kwargs",
            "or_parts",
            # FIXME:
            # If we add c_stmts, we can miss adding a c_stmt,
            # test_float.py test_set_format() is an example.
            # Investigate
            # "c_stmts",
            "stmts",
            # Python 3.7+
            "importlist37",
        ]
        self.collect = frozenset(nt_list)

        # For these items we need to keep the 1st epslion reduction since
        # the nonterminal name is used in a semantic action.
        self.keep_epsilon = frozenset(("kvlist_n", "kvlist"))

        # ??? Do we need a debug option to skip eliding singleton reductions?
        # Time will tell if it if useful in debugging

        # FIXME: optional_nt is a misnomer. It's really about there being a
        # singleton reduction that we can simplify. It also happens to be optional
        # in its other derivation
        self.optional_nt |= frozenset(("suite_stmts", "c_stmts_opt", "stmt", "sstmt"))

        # Reduce singleton reductions in these nonterminals:
        # FIXME: would love to do expr, sstmts, stmts and
        # so on but that would require major changes to the
        # semantic actions
        self.singleton = frozenset(
            ("str", "store", "_stmts", "suite_stmts_opt", "inplace_op")
        )
        # Instructions filled in from scanner
        self.insts = []

        # true if we are parsing inside a lambda expression.
        # because a lambda expression are written on a single line, certain line-oriented
        # statements behave differently
        self.is_lambda = False
