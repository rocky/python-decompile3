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
            "ifelsestmtc",
            (
                "testexpr",
                "c_stmts_opt",
                "jb_elsec",
                "else_suitec"
            ),
        ),
        (
            "ifelsestmtc",
            (
                "testexpr",
                "c_stmts_opt",
                "jb_cfs",
                "else_suitec"
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
                "else_suite",
                "\\e__come_froms",
            ),
        ),
    ):
        return False

    # Make sure all of the "come froms" offset at the
    # end of the "if" come from somewhere inside the "if".
    # Since the come_froms are ordered so that lowest
    # offset COME_FROM is last, it is sufficient to test
    # just the last one.
    if len(ast) == 5:
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
        assert else_suite in ("else_suite", "else_suitec")

        if else_suite == "else_suitec" and ast[2] in ("jb_elsec", "jbcfs"):
            stmts = ast[1]
            jb_else = ast[2]
            come_from = jb_else[-1]
            assert come_from == "COME_FROM"
            if come_from.attr > stmts.first_child().off2int():
                return True

        if len(test) > 1 and test[1].kind.startswith("jmp_"):
            if last == n:
                last -= 1

            jmp = test[1]
            jmp_target = jmp[0].attr

            # Below we check that jmp_target is jumping to a feasible
            # location. It should be to the transition after the "then"
            # block and to the beginning of the "else" block.
            # However the "if/else" is inside a loop the false test can be
            # back to the loop.

            # FIXME: the below logic for jf_cfs could probably be
            # simplified.
            jump_else_end = ast[2]
            last_offset = tokens[last].off2int(prefer_last=False)
            if (
                jump_else_end in ("jf_cfs", "jump_forward_else")
                and jump_else_end[0] == "JUMP_FORWARD"
            ):
                # If the "else" jump jumps before the end of the the "if .. else end", then this
                # is not this kind of "ifelsestmt".
                jump_else_forward = jump_else_end[0]
                jump_else_forward_target = jump_else_forward.attr
                if jump_else_forward_target < last_offset:
                    return True

                # If tokens[last] is a COME_FROM, it has to come from
                # the jump_else forward.

                # Since offset values can be funky strings, the
                # most reliable is to check on COME_FROM attr field
                # which will always be an integer instruction offset.
                # Also the else jump-forward offset should be an int
                # (not a string) since that comes from the original
                # bytecode and wasn't an added instruction.
                if (
                    tokens[last] == "COME_FROM"
                    and tokens[last].attr == jump_else_forward.off2int(prefer_last=True)
                ):
                    return False
            if (
                jump_else_end in ("jb_elsec", "jf_cfs", "jb_cfs") and
                jump_else_end[-1] == "COME_FROM"
            ):
                return jump_else_end[-1].off2int() != jmp_target

            if tokens[first].off2int() > jmp_target:
                return True

            return (jmp_target > last_offset) and tokens[last] != "JUMP_FORWARD"

    return False
