# Adapted from issue decompyle3 #40
# The bug is having a return in the except clause
# 3.8 adds a POP_EXCEPT before the return and that
# causes havoc.

"""This program is self-checking!"""


def try_except1(a):
    try:
        10 / a
        return True
    except:
        return False


assert try_except1(1)
assert not try_except1(0)

# Adapted from uncompyle6 #368
def try_except2(a):
    try:
        10 / a
    except:
        return False


assert try_except2(1) is None
assert try_except2(0) is False


def try_except3(a):
    try:
        10 / a
    except:
        x = a == 0
        return x


assert try_except3(1) is None
assert try_except3(0) is True


def try_except4(a):
    try:
        10 / a
    except ZeroDivisionError:
        x = a == 0
        return x


assert try_except4(1) is None
assert try_except4(0) is True
