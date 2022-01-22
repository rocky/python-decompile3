#  Copyright (c) 2020 Rocky Bernstein


def testtrue(self, lhs: str, n: int, rule, ast, tokens, first: int, last: int) -> bool:
    # FIXME: make this work for all versions
    if self.version != 3.7:
        return False
    if rule == ("testtrue", ("expr", "POP_JUMP_IF_TRUE")):
        pjit = tokens[min(last - 1, n - 2)]
        # If we have a backwards (looping) jump then this is
        # really a testfalse. But "asserts" work funny
        if pjit == "POP_JUMP_IF_TRUE_LOOP":
            assert_next = tokens[min(last + 1, n - 1)]
            return assert_next != "RAISE_VARARGS_1"
    elif rule == ("testfalsec", ("expr", "POP_JUMP_IF_TRUE")):
        pjit = tokens[min(last - 1, n - 2)]
        # If we have a backwards (looping) jump then this is
        # really a testtrue. But "asserts" work funny
        if pjit.kind == "POP_JUMP_IF_TRUE_LOOP":
            assert_next = tokens[min(last + 1, n - 1)]
            return assert_next == "RAISE_VARARGS_1"
    return False
