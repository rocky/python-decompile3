#  Copyright (c) 2020 Rocky Bernstein

def or_cond_check(
    self, lhs: str, n: int, rule, ast, tokens: list, first: int, last: int
) -> bool:
    if rule == ("or_cond", ("or_parts", "expr_pjif", "come_froms")):
        if tokens[last-1] == "COME_FROM":
            return tokens[last-1].attr < tokens[first].offset
    return False
