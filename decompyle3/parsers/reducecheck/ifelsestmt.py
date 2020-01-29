#  Copyright (c) 2020 Rocky Bernstein

from decompyle3.scanners.tok import Token


def ifelsestmt(
    self, lhs: str, n: int, rule, ast, tokens: list, first: int, last: int
) -> bool:

    if (last + 1) < n and tokens[last + 1] == "COME_FROM_LOOP":
        # ifelsestmt jumped outside of loop. No good.
        return True

    if rule not in (
        (
            "ifelsestmt",
            (
                "testexpr",
                "stmts_opt",
                "jump_forward_else",
                "else_suite",
                "_come_froms",
            ),
        ),
        (
            "ifelsestmt",
            (
                "testexpr",
                "stmts_opt",
                "jump_forward_else",
                "else_suite",
                "\\e__come_froms",
            ),
        ),
        (
            "ifelsestmt",
            (
                "testexpr",
                "stmts_opt",
                "jf_cfs",
                "else_suite",
                "\\e_opt_come_from_except",
            ),
        ),
        (
            "ifelsestmt",
            ("testexpr", "stmts", "come_froms", "else_suite", "come_froms",),
        ),
        (
            "ifelsestmt",
            (
                "testexpr",
                "stmts_opt",
                "jf_cfs",
                "else_suite",
                "opt_come_from_except",
            ),
        ),
        (
            "ifelsestmt",
            (
                "testexpr",
                "stmts_opt",
                "jump_forward_else",
                "else_suite", "\\e__come_froms",
            ),
        )
    ):
        return False

    # Make sure all of the "come froms" offset at the
    # end of the "if" come from somewhere inside the "if".
    # Since the come_froms are ordered so that lowest
    # offset COME_FROM is last, it is sufficient to test
    # just the last one.
    come_froms = ast[-1]
    if come_froms == "opt_come_from_except" and len(come_froms) > 0:
        come_froms = come_froms[0]
    if not isinstance(come_froms, Token):
        if len(come_froms):
            return tokens[first].offset > come_froms[-1].attr
    elif tokens[first].offset > come_froms.attr:
        return True

    testexpr = ast[0]

    # Check that the condition portion of the "if"
    # jumps to the "else" part.
    if testexpr[0] in ("testtrue", "testfalse"):
        test = testexpr[0]

        else_suite = ast[3]
        assert else_suite == "else_suite"

        if len(test) > 1 and test[1].kind.startswith("jmp_"):
            if last == n:
                last -= 1
            jmp = test[1]
            jmp_target = jmp[0].attr

            # FIXME: the jump inside "else" check below should be added.
            #
            # add this until we can find out what's wrong with
            # not being able to parse:
            #     if a and b or c:
            #         x = 1
            #     else:
            #         x = 2

            # FIXME: add this
            # if jmp_target < else_suite.first_child().off2int():
            #     return True

            # FIXME: the below logic for jf_cfs could probably be
            # simplified.
            jump_else_end = ast[2]
            last_offset = tokens[last].off2int(prefer_last=False)
            # if jump_else_end == "jump_forward_else" and (first, last) == (0, 13):
            #     from trepan.api import debug; debug()
            if jump_else_end in ("jf_cfs", "jump_forward_else") and jump_else_end[0] == "JUMP_FORWARD":
                # else end jumps before the end of the the "if .. else end"?
                jump_else_end_offset = jump_else_end[0].attr
                if jump_else_end_offset < last_offset:
                    return True

                # If we have a COME_FROM that follows, it must be
                # from the jump_else_end, otherwise this is no good.
                #
                if tokens[last-1] == "COME_FROM":
                    if tokens[last-1].attr == jump_else_end[0].offset and tokens[last] == "COME_FROM":
                        return False

                # When the final instruction is a COME_FROM we need
                # to adjust last. Note it was adjusted in this specfic
                # case in the caller.
                if n - 1  == last and tokens[last] == "COME_FROM":
                    return tokens[last].attr != jump_else_end[0].offset

            if tokens[first].off2int() > jmp_target:
                return True

            return (jmp_target > last_offset) and tokens[last] != "JUMP_FORWARD"

    return False
