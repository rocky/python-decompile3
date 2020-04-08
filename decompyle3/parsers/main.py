#  Copyright (c) 2019-2020 Rocky Bernstein
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
Common decompyle3 parser routines. From the outside, of the module
you'll usually import a call something here, such as:
* python_parser(), or
* parse()
or import a base class such as:

*ParseError(),
* PythonLambdaParser(), or
* PythonParser()

Note however all of this is imported from the __init__ module
"""

import sys

from xdis.code import iscode
from xdis.magics import py_str2float
from spark_parser import GenericASTBuilder, DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from decompyle3.show import maybe_show_asm


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

def nop_func(self, args):
    return None


class PythonLambdaParser(GenericASTBuilder):
    def __init__(self, SyntaxTree, start_symbol, debug):
        super(PythonLambdaParser, self).__init__(SyntaxTree, start_symbol, debug)
        # FIXME: customize per python parser version

        # These are the non-terminals we should collect into a list.
        # For example instead of:
        #   stmts -> stmts stmt -> stmts stmt stmt ...
        # collect as stmts -> stmt stmt ...
        nt_list = [
            "_come_froms",
            "attributes",
            "come_froms",
            "exprlist",
            "kvlist",
            "kwargs",
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
        self.optional_nt |= frozenset(
            ("come_froms", "suite_stmts", "c_stmts_opt", "stmt", "sstmt")
        )

        # Reduce singleton reductions in these nonterminals:
        # FIXME: would love to do expr, sstmts, stmts and
        # so on but that would require major changes to the
        # semantic actions
        self.singleton = frozenset(("str", "store", "inplace_op"))
        # Instructions filled in from scanner
        self.insts = []

        # true if we are parsing inside a lambda expression.
        # because a lambda expression are wrtten on a single line, certain line-oriented
        # statements behave differently
        self.is_lambda = True

    def ast_first_offset(self, ast):
        if hasattr(ast, "offset"):
            return ast.offset
        else:
            return self.ast_first_offset(ast[0])

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
        if start > 0:
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
        # Low byte indicates number of positional paramters,
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
        # print >> sys.stderr, 'resolve', str(list)
        return GenericASTBuilder.resolve(self, list)


class PythonParser(PythonLambdaParser):
    def __init__(self, SyntaxTree, compile_mode, debug):
        # FIXME: Not sure if start symbol is correct for "single"
        if compile_mode in ("exec", "single"):
            start_symbol = "stmts"
        # FIXME: "eval" should be "lambda"
        elif compile_mode == "lambda":
            start_symbol = "lambda_start"
        elif compile_mode == "eval":
            start_symbol = "call_stmt"
        elif compile_mode == "eval_expr":
            start_symbol = "eval_expr"
        else:
            raise BaseException(f'compile_mode should be either "exec", "single", "lambda", or "eval"; got {compile_mode}')

        if compile_mode in ("eval", "expr"):
            PythonParserEval.__init__(self, SyntaxTree, start_symbol, debug)
        else:
            PythonLambdaParser.__init__(self, SyntaxTree, start_symbol, debug)

        # FIXME: customize per python parser version

        # These are the non-terminals we should collect into a list.
        # For example instead of:
        #   stmts -> stmts stmt -> stmts stmt stmt ...
        # collect as stmts -> stmt stmt ...
        nt_list = [
            "_come_froms",
            "_stmts",
            "attributes",
            "come_froms",
            "except_stmts",
            "exprlist",
            "importlist",
            "kvlist",
            "kwargs",
            # FIXME:
            # If we add c_stmts, we can miss adding a c_stmt,
            # test_float.py test_set_format() is an example.
            # Investigate
            # "c_stmts",
            "stmts",
            # Python 3.6+
            "come_from_loops",
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
        self.optional_nt |= frozenset(
            ("come_froms", "suite_stmts", "c_stmts_opt", "stmt", "sstmt")
        )

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
        # because a lambda expression are wrtten on a single line, certain line-oriented
        # statements behave differently
        self.is_lambda = False


def parse(p, tokens, customize, is_lambda):
    was_lambda = p.is_lambda
    p.is_lambda = is_lambda
    p.customize_grammar_rules(tokens, customize)
    ast = p.parse(tokens)
    p.is_lambda = was_lambda
    #  p.cleanup()
    return ast


def get_python_parser(
    version, debug_parser=PARSER_DEFAULT_DEBUG, compile_mode="exec", is_pypy=False
):
    """Returns parser object for Python version 3.7, 3.8,
    etc., depending on the parameters passed.  *compile_mode* is either
    "exec", "eval", or "single" or "lambda".

    "lambda" is for the grammar that can appear in lambda statements. "eval"
    is for eval kinds of expressions.

    For the others, see https://docs.python.org/3/library/functions.html#compile for an
    explanation of the different modes.

    """

    # If version is a string, turn that into the corresponding float.
    if isinstance(version, str):
        version = py_str2float(version)

    # FIXME: there has to be a better way...
    # We could do this as a table lookup, but that would force us
    # in import all of the parsers all of the time. Perhaps there is
    # a lazy way of doing the import?

    if version < 3.7:
        raise RuntimeError(f"Unsupported Python version {version}")
    elif version == 3.7:
        import decompyle3.parsers.p37 as parse37

        if compile_mode == "exec":
            p = parse37.Python37Parser(debug_parser)
        elif compile_mode == "lambda":
            p = parse37.Python37LambdaParser(debug_parser, compile_mode=compile_mode)
            ## If the above gives a parse error, use the below to debug what grammar rule(s)
            ## need to get added
            # p = parse37.Python37ParserSingle(debug_parser, compile_mode=compile_mode)
        elif compile_mode == "eval":
            p = parse37.Python37ParserEval(debug_parser, compile_mode="eval_expr")
        else:
            p = parse37.Python37ParserSingle(debug_parser, compile_mode=compile_mode)
    elif version == 3.8:
        import decompyle3.parsers.p38 as parse38

        if compile_mode == "exec":
            p = parse38.Python38Parser(debug_parser)
        elif compile_mode == "lambda":
            p = parse38.Python38LambdaParser(debug_parser, compile_mode=compile_mode)
            ## If the above gives a parse error, use the below to debug what grammar rule(s)
            ## need to get added
            # p = parse38.Python38ParserSingle(debug_parser, compile_mode=compile_mode)
        elif compile_mode == "eval":
            p = parse38.Python38ParserEval(debug_parser, compile_mode="eval_expr")
        else:
            p = parse38.Python38ParserSingle(debug_parser, compile_mode=compile_mode)

    p.version = version
    # p.dump_grammar() # debug
    return p


class PythonParserSingle(PythonParser):
    # FIXME: Remove rules from parse37, parse38
    def p_single_start_rule(self, args):
        """
        # single-mode compilation. Eval-mode interactive compilation
        # drops the last rule.

        call_stmt ::= expr PRINT_EXPR
        """

    pass


class PythonParserEval(PythonLambdaParser):
    def p_eval_start_rule(self, args):
        """
        # eval-mode compilation.  Eval compilation
        # adds another rule.
        eval_expr ::= expr RETURN_VALUE
        """
        # FIXME: add a suitable __init__


def python_parser(
    version: str,
    co,
    out=sys.stdout,
    showasm=False,
    parser_debug=PARSER_DEFAULT_DEBUG,
    is_pypy=False,
    is_lambda=False,
):
    """
    Parse a code object to an abstract syntax tree representation.

    :param version:         The python version this code is from as a float, for
                            example 2.6, 2.7, 3.2, 3.3, 3.4, 3.5 etc.
    :param co:              The code object to parse.
    :param out:             File like object to write the output to.
    :param showasm:         Flag which determines whether the disassembled and
                            ingested code is written to sys.stdout or not.
    :param parser_debug:    dict containing debug flags for the spark parser.

    :return: Abstract syntax tree representation of the code object.
    """

    assert iscode(co)
    from decompyle3.scanner import get_scanner

    scanner = get_scanner(version, is_pypy)
    tokens, customize = scanner.ingest(co)
    maybe_show_asm(showasm, tokens)

    # For heavy grammar debugging
    # parser_debug = {'rules': True, 'transition': True, 'reduce' : True,
    #                 'showstack': 'full'}
    p = get_python_parser(version, parser_debug)
    return parse(p, tokens, customize, is_lambda)


if __name__ == "__main__":

    def parse_test(co) -> None:
        from decompyle3 import IS_PYPY

        ast = python_parser("3.8.1", co, showasm=True, is_pypy=IS_PYPY)
        print(ast)
        return

    parse_test(parse_test.__code__)
