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

# Make sure to list Python38... classes first so we prefer to inherit methods from that first.
# In particular methods like reduce_is_invalid() need to come from there rather than
# a more generic place.


class Python38ParserEval(Python38LambdaParser, PythonParserEval):
    def __init__(self, debug_parser):
        PythonParserEval.__init__(self, debug_parser)


class Python38ParserExec(Python38Parser, PythonParserExec):
    def __init__(self, debug_parser):
        PythonParserExec.__init__(self, debug_parser)


class Python38ParserExpr(Python38Parser, PythonParserExpr):
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
