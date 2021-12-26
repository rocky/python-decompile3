"""
All of the specific kinds of canned parsers for Python 3.8

These are derived from "compile-modes" but we have others that
can be used to parse common part of a larger grammar.

For example:
* a basic-block expression (no branching)
* an unadorned expression (no POP_TOP needed afterwards)
* A non-compound statement
"""
from decompyle3.parsers.p38.full import Python38Parser
from decompyle3.parsers.p38.lambda_expr import Python38LambdaParser
from decompyle3.parsers.parse_heads import (
    PythonParserEval,
    PythonParserExec,
    PythonParserExpr,
    PythonParserLambda,
    PythonParserSingle,
    # FIXME: add
    # PythonParserSimpleStmt
    # PythonParserStmt
)


class Python38ParserEval(PythonParserEval, Python38LambdaParser):
    def __init__(self, debug_parser):
        PythonParserEval.__init__(self, debug_parser)


class Python38ParserExec(PythonParserExec, Python38Parser):
    def __init__(self, debug_parser):
        PythonParserExec.__init__(self, debug_parser)


class Python38ParserExpr(PythonParserExpr, Python38Parser):
    def __init__(self, debug_parser):
        PythonParserExpr.__init__(self, debug_parser)


# Understand: Python38LambdaParser has to come before PythonParserLambda or we get a
# MRO failure
class Python38ParserLambda(Python38LambdaParser, PythonParserLambda):
    def __init__(self, debug_parser):
        PythonParserLambda.__init__(self, debug_parser)


# These classes are here just to get parser doc-strings for the
# various classes inherited properly and start_symbols set properly.
class Python38ParserSingle(Python38Parser, PythonParserSingle):
    def __init__(self, debug_parser):
        PythonParserSingle.__init__(self, debug_parser)
