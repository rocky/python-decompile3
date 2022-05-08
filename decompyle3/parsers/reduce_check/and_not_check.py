#  Copyright (c) 2020 Rocky Bernstein


def and_not_check(
    self, lhs: str, n: int, rule, ast, tokens: list, first: int, last: int
) -> bool:
    if ast[0] == "expr_pjif":
        jmp = ast[0][1]
    else:
        jmp = ast[1]
    if jmp.kind.startswith("POP_JUMP_IF_"):
        if last == n:
            return True
        jump_target = jmp.attr

        if tokens[first].off2int() <= jump_target < tokens[last].off2int():
            return True
        if rule == ("and_not", ("expr_pjif", "expr_pjit")):
            jmp2_target = ast[1][1].attr
            return jump_target != jmp2_target
        return jump_target != tokens[last].off2int()
    return False
