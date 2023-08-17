#  Copyright (c) 2020, 2023 Rocky Bernstein


def if_not_stmtc_invalid(
    self, lhs: str, n: int, rule, tree, tokens: list, first: int, last: int
) -> bool:
    assert len(tree) >= 2
    testexprc, ifstmts_jumpc = tree[:2]

    if testexprc != "testexprc" or ifstmts_jumpc != "ifstmts_jumpc":
        return False

    # print("XXX1", testexprc)
    # print("XXX2", ifstmts_jumpc)

    # Make sure the testexprc does not jump inside the "then"
    last_offset = tokens[last].off2int()
    then_jump = testexprc.last_child()
    if not then_jump.kind.startswith("POP_JUMP_IF_"):
        return False
    then_jump_offset = then_jump.attr
    # print("XXX", then_jump)
    # print("XXX", then_jump_offset, "<=", last_offset)

    if then_jump_offset <= last_offset:
        return True
    return False
