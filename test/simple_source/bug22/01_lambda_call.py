# From https://github.com/rocky/python-uncompyle6/issues/350
# This is RUNNABLE!

"""This program is self-checking!"""

a = (lambda x: x)(abs)  # noqa
assert a(-3) == 3

# From 3.7 test_grammar.py line 647
l4 = lambda x=lambda y=lambda z=1: z: y(): x()  # noqa
assert l4() == 1
