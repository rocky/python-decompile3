# Bugs involving: not and not or
# https://github.com/rocky/python-uncompyle6/issues/326

# Bug was not having rules for "not and not"...
# This file is RUNNABLE!
"""This program is self-checking!"""


def t1(x, y, z):
    while not x and not y or z:
        return True
    return False


def t2(x, y, z):
    if not x and not y or z:
        return True
    return False


for triplet, expect in (
    ((True, True, True), True),
    ((True, True, False), False),
    ((True, False, True), True),
    ((True, False, False), False),
    ((False, True, True), True),
    ((False, True, False), False),
    ((False, False, True), True),
    ((False, False, False), True),
):
    assert t1(*triplet) == expect
    assert t2(*triplet) == expect
