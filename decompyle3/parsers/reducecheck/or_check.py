#  Copyright (c) 2020 Rocky Bernstein


ASSERT_OPS = frozenset(["LOAD_ASSERT", "RAISE_VARARGS_1"])

def or_check(
    self, lhs: str, n: int, rule, ast, tokens: list, first: int, last: int
) -> bool:
    if rule == ("or", ("expr", "jump_if_true", "expr")):
        if tokens[last] in ASSERT_OPS or tokens[last-1] in ASSERT_OPS:
            return True

        # The following test is be the most accurate. It prevents "or" from being
        # mistake for part of an "assert".
        # There one might conceivably be "expr or AssertionError" code, but the
        # likelihood of that is vanishingly small.
        # The below then is useful until we get better control-flow analysis.
        # Note it is too hard in the scanner right nowto turn the LOAD_GLOBAL into
        # int LOAD_ASSERT, however in 3.9ish code generation does this by default.
        load_global = tokens[last - 1]
        if load_global == "LOAD_GLOBAL" and load_global.attr == "AssertionError":
            return True

        first_offset = tokens[first].off2int()
        jump_if_true_target = ast[1][0].attr
        if jump_if_true_target < first_offset:
            return False

        jump_if_false = tokens[last]
        # If the jmp is backwards
        if jump_if_false == "POP_JUMP_IF_FALSE":
            jump_if_false_offset = jump_if_false.off2int()
            if jump_if_false.attr < jump_if_false_offset:
                # For a backwards loop, well compare to the instruction *after*
                # then POP_JUMP...
                jump_if_false = tokens[last + 1]
            return not (
                (jump_if_false_offset <= jump_if_true_target <= jump_if_false_offset + 2)
                or jump_if_true_target < tokens[first].off2int()
            )

    return False
