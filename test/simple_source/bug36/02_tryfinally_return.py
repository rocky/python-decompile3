# Python 3.6 sometimes omits END_FINALLY. See issue #182
def foo():
    try:
        x = 1
    finally:
        return

# from 3.7.6 test_generators.py
def g1():
    try:
        pass
    finally:
        return 1
