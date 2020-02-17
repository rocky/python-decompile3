#  Copyright (c) 2020 Rocky Bernstein

def break_check(
    self, lhs: str, n: int, rule, ast, tokens: list, first: int, last: int
) -> bool:

    if rule[1] != ("POP_EXCEPT", "JUMP_FORWARD"):
        return False

    # Look for a JUMP_BACK instruction either after
    # the end of this rule or before the place where
    # we JUMP_FORWARD to
    if last + 1 < n and tokens[last + 1] == "JUMP_BACK":
        return False

    # FIXME: put jump_back classifcation in a subroutine. Preferably in xdis.
    jump_target_prev = self.insts[self.offset2inst_index[tokens[first+1].attr]-1]
    is_jump_back = (
        jump_target_prev.optype == "jabs"
        and jump_target_prev.arg < jump_target_prev.offset
        )
    return not is_jump_back
