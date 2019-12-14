# from 3.7 decompyle3/pytest/validate.py
# 3.7 changes changes "and" to use JUMP_IF_FALSE_OR_POP instead of
# POP_JUMP_IF_FALSE

# RUNNABLE!
def are_instructions_equal(a, b, c, d):
    return a and (b or c) and d

for a, b, c, d, expect in (
        (True, True, False, True, True),
        (True, False, True, True, True),
        (False, False, True, True, False),
        (True, False, True, False, False),
        ):
    assert are_instructions_equal(a, b, c, d) == expect
