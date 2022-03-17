#  Copyright (c) 2020 Rocky Bernstein


def not_or_check(
    self, lhs: str, n: int, rule, ast, tokens: list, first: int, last: int
) -> bool:

    # Note (exp1 and exp2) and (not exp1 or exp2) are close, especially in
    # an control structure like an "if".
    # "exp1 and exp2":
    #   exp1; POP_JUMP_IF_FALSE endif; exp2; POP_JUMP_IF_FALSE endif; then
    #
    # "not exp1 or exp2":
    #   exp1; POP_JUMP_IF_FALSE then; exp2 POP_JUMP_IF_FALSE endif; then

    # The difference is whether the POP_JUMPs go to the same place or not.

    expr_pjif = ast[0]

    end_token = tokens[last - 1]
    if end_token.kind.startswith("POP_JUMP_IF_FALSE"):

        while expr_pjif == "and_parts":
            expr_pjif = expr_pjif[0]
            pass
        assert expr_pjif == "expr_pjif"
        if expr_pjif[-1].attr != end_token.attr:
            return True

        # More "and" in a condition vs. "not or":
        # Intuitively it has to do with where we go with the "and" or
        # "not or". Right now if there are loop jumps involved
        # we are saying this is "and", but this empirical and not on
        # solid ground.

        # If test jump is a backwards then, we have an "and", not a "not or".
        first_offset = tokens[first].off2int()
        if end_token.attr < first_offset:
            return True
        # Similarly if the test jump goes to another jump it is (probably?) an "and".
        jump_target_inst_index = self.offset2inst_index[end_token.attr]
        inst = self.insts[jump_target_inst_index - 1]
        return inst.is_jump()
        pass
    return False
