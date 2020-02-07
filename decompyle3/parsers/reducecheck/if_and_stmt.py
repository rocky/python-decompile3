#  Copyright (c) 2020 Rocky Bernstein


def if_and_stmt(
    self, lhs: str, n: int, rule, ast, tokens: list, first: int, last: int
) -> bool:
    # Make sure jumps don't extend beyond the end of the if statement.
    last_offset = tokens[last].off2int()
    for i in range(first, last):
        t = tokens[i]
        # instead of POP_JUMP_IF, should we use op attributes?
        if t.kind in ("POP_JUMP_IF_FALSE", "POP_JUMP_IF_TRUE"):
            pjif_target = t.attr
            if pjif_target > last_offset:
                # In come cases, where we have long bytecode, a
                # "POP_JUMP_IF_TRUE/FALSE" offset might be too
                # large for the instruction; so instead it
                # jumps to a JUMP_FORWARD. Allow that here.
                if tokens[last] == "JUMP_FORWARD":
                    return tokens[last].attr != pjif_target
                return True
            elif lhs == "ifstmtc" and tokens[first].off2int() > pjif_target:
                # A conditional JUMP to the loop is expected for "ifstmtc"
                return False
            pass
        pass
    pass

    if not ast:
        return False

    end_if_jump = ast[1]
    end_if_offset = end_if_jump.attr
    # stmts = ast[-2]
    # come_froms = ast[-1]
    return end_if_offset < tokens[last].off2int(prefer_last=False)
