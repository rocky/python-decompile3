#  Copyright (c) 2020, 2023 Rocky Bernstein

from decompyle3.scanners.tok import Token


def ifstmts_jump_invalid(
    self, lhs: str, n: int, rule, tree, tokens: list, first: int, last: int
) -> bool:

    come_froms = tree[-1]
    # This is complicated, but note that the JUMP_IF instruction comes immediately
    # *before* _ifstmts_jump so that's what we have to test
    # the COME_FROM against. This can be complicated by intervening
    # POP_TOP, and pseudo COME_FROM, ELSE instructions
    #
    pop_jump_index = first - 1
    while pop_jump_index > 0 and tokens[pop_jump_index] in (
        "POP_TOP",
        "JUMP_FORWARD",
        "COME_FROM",
    ):
        pop_jump_index -= 1

    if pop_jump_index == 0:
        return True

    jump_token = tokens[pop_jump_index]
    if jump_token.op not in self.opc.JUMP_OPS:
        return False

    # FIXME: something is fishy when and EXTENDED ARG is needed before the
    # pop_jump_index instruction to get the argument. In this case, the
    # _ifsmtst_jump can jump to a spot beyond the come_froms.
    # That is going on in the non-EXTENDED_ARG case is that the POP_JUMP_IF
    # jumps to a JUMP_(FORWARD) which is changed into an EXTENDED_ARG POP_JUMP_IF
    # to the jumped forwarded address
    if jump_token.attr > 256:
        return False

    pop_jump_offset = jump_token.off2int(prefer_last=False)
    if isinstance(come_froms, Token):
        if jump_token.attr < pop_jump_offset and tree[0] != "pass":
            # This is a jump backwards to a loop. All bets are off here when there the
            # unless statement is "pass" which has no instructions associated with it.
            return False
        return come_froms.attr is not None and pop_jump_offset > come_froms.attr

    elif len(come_froms) == 0:
        return False
    else:
        return pop_jump_offset > come_froms[-1].attr
