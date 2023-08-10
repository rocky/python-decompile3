# From 3.8 test_gc.py
# RUNNABLE!

"""This program is self-checking!"""


def test_bug1055820c(detector, i):
    while not detector:
        i += 1
        if i > 10000:
            i = 10
        detector = 30
    return detector


assert test_bug1055820c(0, 6) == 30
assert test_bug1055820c(1, 6) == 1
