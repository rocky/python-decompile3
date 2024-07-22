"""
Here we have checks done before a grammar rule reduction for that nonterminal takes place.

These check the validity of rule reduction based on properties that aren't in
the tokens. These checks basically have full access to everything.
Optionally, it can have access to the tree built for the reduction nonterminal
it checks.
"""


from decompyle3.parsers.reduce_check.and_check import and_invalid
from decompyle3.parsers.reduce_check.and_cond_check import and_cond_check
from decompyle3.parsers.reduce_check.and_not_check import and_not_check
from decompyle3.parsers.reduce_check.break38_check import break_invalid
from decompyle3.parsers.reduce_check.c_tryelsestmt import *  # noqa
from decompyle3.parsers.reduce_check.for38_check import for38_invalid
from decompyle3.parsers.reduce_check.forelse38_check import forelse38_invalid
from decompyle3.parsers.reduce_check.if_and_elsestmt import *  # noqa
from decompyle3.parsers.reduce_check.if_and_stmt import if_and_stmt
from decompyle3.parsers.reduce_check.if_not_stmtc import if_not_stmtc_invalid
from decompyle3.parsers.reduce_check.ifelsestmt import ifelsestmt
from decompyle3.parsers.reduce_check.iflaststmt import *  # noqa
from decompyle3.parsers.reduce_check.ifstmt import *  # noqa
from decompyle3.parsers.reduce_check.ifstmts_jump import ifstmts_jump_invalid
from decompyle3.parsers.reduce_check.lastc_stmt import *  # noqa
from decompyle3.parsers.reduce_check.list_if_not import *  # noqa
from decompyle3.parsers.reduce_check.not_or_check import *  # noqa
from decompyle3.parsers.reduce_check.or_check import *  # noqa
from decompyle3.parsers.reduce_check.or_cond_check import *  # noqa
from decompyle3.parsers.reduce_check.pop_return import pop_return_check
from decompyle3.parsers.reduce_check.testtrue import *  # noqa
from decompyle3.parsers.reduce_check.tryexcept import *  # noqa
from decompyle3.parsers.reduce_check.while1elsestmt import *  # noqa
from decompyle3.parsers.reduce_check.while1stmt import *  # noqa
from decompyle3.parsers.reduce_check.whilestmt import *  # noqa
from decompyle3.parsers.reduce_check.whilestmt38 import whilestmt38_check
from decompyle3.parsers.reduce_check.whileTruestmt38 import *  # noqa

__all__ = [
    "and_invalid",
    "and_cond_check",
    "and_not_check",
    "break_invalid",
    "for38_invalid",
    "forelse38_invalid",
    "if_and_stmt",
    "if_not_stmtc_invalid",
    "ifstmts_jump_invalid",
    "ifelsestmt",
    "pop_return_check",
    "whilestmt38_check",
]
