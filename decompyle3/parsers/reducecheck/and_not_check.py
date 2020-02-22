#  Copyright (c) 2020 Rocky Bernstein


def and_not_check(
    self, lhs: str, n: int, rule, ast, tokens: list, first: int, last: int
) -> bool:
    jmp = ast[1]
    if jmp.kind.startswith("jump_if_"):
        if last == n:
            return True
        jump_target = jmp[0].attr

        if tokens[first].off2int() <= jump_target < tokens[last].off2int():
            return True
        if rule == ("and_not", ("expr", "POP_JUMP_IF_FALSE", "expr", "POP_JUMP_IF_TRUE")):
            jmp2_target = ast[3].attr
            return jump_target != jmp2_target
        return jump_target != tokens[last].off2int()
    return False
