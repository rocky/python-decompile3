#  Copyright (c) 2020 Rocky Bernstein


def iflaststmt(
    self, lhs: str, n: int, rule, ast, tokens: list, first: int, last: int
) -> bool:
    testexpr = ast[0]

    # FIXME: should this be done in the caller?
    if tokens[last] == "RETURN_LAST":
        last -= 1

    if testexpr[0] in ("testtrue", "testtruec", "testfalse", "testfalsec"):

        test = testexpr[0]
        if len(test) > 1 and test[1].kind.startswith("jump_if_"):
            if last == n:
                last -= 1
            jump_target = test[1][0].attr
            first_offset = tokens[first].off2int()
            if  first_offset <= jump_target < tokens[last].off2int():
                return True
            # jump_target less than tokens[first] is okay - is to a loop
            # jump_target equal tokens[last] is also okay: normal non-optimized non-loop jump

            if (last + 1) < n:
                if tokens[last - 1] == "JUMP_BACK":
                    if jump_target > first_offset:
                        # The end of the iflaststmt if test jumps backward to a loop
                        # but the false branch of the "if" doesn't also jump back.
                        # No good. This is probably an if/else instead.
                        return True
                    pass
                elif tokens[last + 1] == "COME_FROM_LOOP" and tokens[last] != "BREAK_LOOP":
                    # iflastsmtc is not at the end of a loop, but jumped outside of loop. No good.
                    # FIXME: check that tokens[last] == "POP_BLOCK"? Or allow for it not to appear?
                    return True

            # If the instruction before "first" is a "POP_JUMP_IF_FALSE" which goes
            # to the same target as jump_target, then this not nested "if .. if .."
            # but rather "if ... and ..."
            if first > 0 and tokens[first - 1] == "POP_JUMP_IF_FALSE":
                return tokens[first - 1].attr == jump_target

            if jump_target > tokens[last].off2int():
                if jump_target == tokens[last - 1].attr:
                    # if c1 [jump] jumps exactly the end of the iflaststmt...
                    return False
                # One more weird case to look out for
                #   if c1:
                #      if c2:  # Jumps around the *outer* "else"
                #       ...
                #   else:
                return (lhs == "iflaststmtl" and last < n and tokens[last] == "JUMP_FORWARD")

        pass
    return False
