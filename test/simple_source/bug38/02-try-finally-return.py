# https://github.com/rocky/python-decompile3/issues/67From 3.0 asyncore.py
# This is RUNNABLE!
def try_finally_return1(a):
    x = 3
    try:
        x = 1 / a
    finally:
        y = 2
        return x + y


def try_finally_return2(a):
    x = 2
    try:
        x = 1 / a
    finally:
        return x


assert try_finally_return1(1) == 3
assert try_finally_return1(0) == 5

assert try_finally_return2(1) == 1
assert try_finally_return2(0) == 2
