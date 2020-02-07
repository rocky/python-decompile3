#  Copyright (c) 2020 Rocky Bernstein


def whilestmt(
    self, lhs: str, n: int, rule, ast, tokens: list, first: int, last: int
) -> bool:
    # When we are missing a COME_FROM_LOOP, the
    # "while" statement is nested inside an if/else
    # so after the POP_BLOCK we have a JUMP_FORWARD which forms the "else" portion of the "if"
    # Check this.
    return tokens[last-1] == "POP_BLOCK" and tokens[last] not in ("JUMP_FORWARD", "COME_FROM_LOOP")
