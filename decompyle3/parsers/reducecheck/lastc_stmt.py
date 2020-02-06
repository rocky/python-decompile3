#  Copyright (c) 2020 Rocky Bernstein

from decompyle3.scanners.tok import Token


def lastc_stmt(
    self, lhs: str, n: int, rule, ast, tokens: list, first: int, last: int
) -> bool:
    # A lastc_stmt really has to be the last thing in a block,
    # a statement that doesn't fall through to the next instruction, or
    # in the case of "POP_BLOCK" is about to end.
    # Otherwise this kind of stmt should flow through to the next.
    # However that larger, set of stmts could be a lastc_stmt, but come back
    # here with that lareger set of stmts.
    return tokens[last] not in ("POP_BLOCK", "JUMP_BACK", "COME_FROM_LOOP")
    return False
