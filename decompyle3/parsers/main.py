#  Copyright (c) 2019-2024 Rocky Bernstein
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
* get_python_parser().parse(), or
* python_parser() which does the above

"""

import sys

from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from xdis import iscode
from xdis.version_info import IS_PYPY, PYTHON_VERSION_TRIPLE, version_tuple_to_str

from decompyle3.parsers.p37.heads import (
    Python37ParserEval,
    Python37ParserExec,
    Python37ParserExpr,
    Python37ParserLambda,
    Python37ParserSingle,
)
from decompyle3.parsers.p38.heads import (
    Python38ParserEval,
    Python38ParserExec,
    Python38ParserExpr,
    Python38ParserLambda,
    Python38ParserSingle,
)
from decompyle3.parsers.p38pypy.heads import (
    Python38PyPyParserEval,
    Python38PyPyParserExec,
    Python38PyPyParserExpr,
    Python38PyPyParserLambda,
    Python38PyPyParserSingle,
)
from decompyle3.parsers.treenode import SyntaxTree
from decompyle3.show import maybe_show_asm


def parse(p, tokens, customize, is_lambda: bool) -> SyntaxTree:
    was_lambda = p.is_lambda
    p.is_lambda = is_lambda
    p.customize_grammar_rules(tokens, customize)
    tree = p.parse(tokens)
    p.is_lambda = was_lambda
    #  p.cleanup()
    return tree


def get_python_parser(
    version, debug_parser=PARSER_DEFAULT_DEBUG, compile_mode="exec", is_pypy=False
):
    """
    Returns parser object for Python version 3.7, 3.8, etc. depending on the parameters
    passed.

    *compile_mode* is one of:

    * "lambda": is for the grammar that can appear in lambda statements.
    * "eval_expr:" is for grammar "expr" kinds of expressions - this is a smaller kind
       of "eval" that users only grammar inside lambdas.
    * "eval:" is for Python eval() kinds of expressions or eval compile mode
    * "exec": is for Python exec() kind of expressions, or exec compile mode
    * "single": is python compile "single" compile mode

    See https://docs.python.org/3/library/functions.html#compile for an
    explanation of the different modes.
    """

    # FIXME: there has to be a better way...
    # We could do this as a table lookup, but that would force us
    # in import all of the parsers all of the time. Perhaps there is
    # a lazy way of doing the import?

    version = version[:2]
    if version < (3, 7):
        raise RuntimeError(f"Unsupported Python version {version}")
    elif version == (3, 7):
        if compile_mode == "exec":
            p = Python37ParserExec(debug_parser=debug_parser)
        elif compile_mode == "single":
            p = Python37ParserSingle(debug_parser=debug_parser)
        elif compile_mode == "lambda":
            p = Python37ParserLambda(debug_parser=debug_parser)
        elif compile_mode == "eval":
            p = Python37ParserEval(debug_parser=debug_parser)
        elif compile_mode == "expr":
            p = Python37ParserExpr(debug_parser=debug_parser)
        else:
            p = Python37ParserSingle(debug_parser)
    elif version == (3, 8):
        if compile_mode == "exec":
            if is_pypy:
                p = Python38PyPyParserExec(debug_parser=debug_parser)
            else:
                p = Python38ParserExec(debug_parser=debug_parser)

        elif compile_mode == "single":
            if is_pypy:
                p = Python38PyPyParserSingle(debug_parser=debug_parser)
            else:
                p = Python38ParserSingle(debug_parser=debug_parser)
        elif compile_mode == "lambda":
            if is_pypy:
                p = Python38PyPyParserLambda(debug_parser=debug_parser)
            else:
                p = Python38ParserLambda(debug_parser=debug_parser)
        elif compile_mode == "eval":
            if is_pypy:
                p = Python38PyPyParserEval(debug_parser=debug_parser)
            else:
                p = Python38ParserEval(debug_parser=debug_parser)
        elif compile_mode == "expr":
            if is_pypy:
                p = Python38PyPyParserExpr(debug_parser=debug_parser)
            else:
                p = Python38ParserExpr(debug_parser=debug_parser)
        elif is_pypy:
            p = Python38PyPyParserSingle(debug_parser)
        else:
            p = Python38ParserSingle(debug_parser)

    elif version > (3, 8):
        raise RuntimeError(
            f"""Version {version_tuple_to_str(version)} is not supported."""
        )

    p.version = version
    # p.dump_grammar() # debug
    return p


def python_parser(
    co,
    version: tuple = PYTHON_VERSION_TRIPLE,
    out=sys.stdout,
    showasm: bool = False,
    parser_debug=PARSER_DEFAULT_DEBUG,
    compile_mode: str = "exec",
    is_pypy: bool = False,
    is_lambda: bool = False,
) -> SyntaxTree:
    """
    Parse a code object to an abstract syntax tree representation.

    :param co:              The code object to parse.
    :param version:         The python version of this code is from as a float, for
                            example, 2.6, 2.7, 3.2, 3.3, 3.4, 3.5 etc.
    :param out:             File like object to write the output to.
    :param showasm:         Flag which determines whether the disassembled and
                            ingested code is written to sys.stdout or not.
    :param parser_debug:    dict containing debug flags for the spark parser.
    :param compile_mode:    compile mode that we want to parse input `co` as.
                            This is either "exec", "eval" or, "single".
    :param is_pypy:         True if ``co`` comes is PyPy code
    :param is_lambda        True if ``co`` is a lambda expression

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
    p = get_python_parser(
        version, parser_debug, compile_mode=compile_mode, is_pypy=IS_PYPY
    )

    # FIXME: have p.insts update in a better way
    # modularity is broken here
    p.insts = scanner.insts
    p.offset2inst_index = scanner.offset2inst_index
    p.opc = scanner.opc

    return parse(p, tokens, customize, is_lambda)


if __name__ == "__main__":

    def parse_test(co) -> None:

        tree = python_parser(co, (3, 8, 2), showasm=True, is_pypy=IS_PYPY)
        print(tree)
        print("+" * 30)
        return

    parse_test(parse_test.__code__)
