"""
All of the specific kinds of canned parsers for Python 3.7

These are derived from "compile-modes" but we have others that
can be used to parse common part of a larger grammar.

For example:
* a basic-block expression (no branching)
* an unadorned expression (no POP_TOP needed afterwards)
* A non-compound statement
"""
from decompyle3.parsers.p37.full import Python37Parser
from decompyle3.parsers.p37.lambda_expr import Python37LambdaParser
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
from decompyle3.scanners.tok import Token


# Make sure to list Python37... classes first so we prefer to inherit methods from that first.
# In particular methods like reduce_is_invalid() need to come from there rather than
# a more generic place.


class Python37ParserEval(Python37LambdaParser, PythonParserEval):
    def __init__(self, debug_parser):
        PythonParserEval.__init__(self, debug_parser)


class Python37ParserExec(Python37Parser, PythonParserExec):
    def __init__(self, debug_parser):
        PythonParserExec.__init__(self, debug_parser)


class Python37ParserExpr(Python37Parser, PythonParserExpr):
    def __init__(self, debug_parser):
        PythonParserExpr.__init__(self, debug_parser)


class Python37ParserLambda(Python37LambdaParser, PythonParserLambda):
    def __init__(self, debug_parser):
        PythonParserLambda.__init__(self, debug_parser)

    def reduce_is_invalid(self, rule, ast, tokens, first, last):
        if rule[0] == "call_kw":
            # Make sure we don't derive call_kw
            nt = ast[0]
            while not isinstance(nt, Token):
                if nt[0] == "call_kw":
                    return True
                nt = nt[0]
                pass
            pass
        return False


# These classes are here just to get parser doc-strings for the
# various classes inherited properly and start_symbols set pproperly
class Python37ParserSingle(Python37Parser, PythonParserSingle):
    def __init__(self, debug_parser):
        PythonParserSingle.__init__(self, debug_parser)
