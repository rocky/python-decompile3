# Issue 478 of uncompile
"This file is self checking"
# Problem was confusing "a or not b" with
# its negation: "not a or b".


def testit(a, b):
    if a or not b:
        return True
    return False


assert testit(True, True) is True
assert testit(True, False) is True
assert testit(False, True) is False
assert testit(False, False) is True
