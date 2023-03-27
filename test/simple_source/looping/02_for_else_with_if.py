# Issue 121
# We need to distinguish:
#  "if_not_stmtc testtruec" with a POP_JUMP_IF_FALSE LOOP (invalid)
# from:
#  "if_stmtc testtruec" with a POP_JUMP_IF_FALSE LOOP (valid)
# In the next decompiler iteration this will be done more cleanly
#
# RUNNABLE!

"""This program is self-checking!"""


def for_else_with_if(forbidden, parts):
    for name in forbidden:
        if name in parts:
            return True
    else:
        return False


assert for_else_with_if({1, 2}, {1, 2})
assert not for_else_with_if({1, 2}, {})
