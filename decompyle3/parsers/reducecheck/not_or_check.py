#  Copyright (c) 2020 Rocky Bernstein


def not_or_check(
    self, lhs: str, n: int, rule, ast, tokens: list, first: int, last: int
) -> bool:
    end_token = tokens[last-1]

    # FIXME: we need a better way to cateragorize "and" vs. "not or".
    # Intuitively it has to do with where we go with the "and" or
    # "not or" is false. Right now if there are loop jumps involved
    # we are saying this is "and", but this empirical and not on
    # solid ground.

    # If test jump is a backwards then, we have an "and", not a "not or".
    if end_token == "POP_JUMP_IF_FALSE":
        first_offset = tokens[first].off2int()
        if end_token.attr < first_offset:
            return True
        # Similarly if the test jump goes after a backwards jump it is an "and".
        jump_target_inst_index = self.offset2inst_index[end_token.attr]
        inst = self.insts[jump_target_inst_index-1]
        return inst.optype == "jabs" and inst.arg < first_offset
        pass
    return False
