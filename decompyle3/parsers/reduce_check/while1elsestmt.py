#  Copyright (c) 2020-2021 Rocky Bernstein


def while1elsestmt(
    self, lhs: str, n: int, rule, ast, tokens: list, first: int, last: int
) -> bool:
    if last == n:
        # Adjust for fuzziness in parsing
        last -= 1

    if tokens[last] == "COME_FROM_LOOP":
        last -= 1
    elif tokens[last - 1] == "COME_FROM_LOOP":
        last -= 2
    if tokens[last] in ("JUMP_LOOP", "CONTINUE"):
        # These indicate inside a loop, but token[last]
        # should not be in a loop.
        # FIXME: Not quite right: refine by using target
        return True

    # if SETUP_LOOP target spans the else part, then this is
    # not while1else. Also do for whileTrue?
    last += 1
    # 3.8+ Doesn't have SETUP_LOOP
    return self.version < (3, 8) and tokens[first].attr > tokens[last].off2int()
