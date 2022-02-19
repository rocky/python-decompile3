# Bug in &= ~x in Python 3
# subscript2 Uses DUP_TOP_TWO in Python 3 and
# DUP_TOPX_2 in Python 2

"""This program is self-checking!"""

old = list(range(3))
new = old[:]
assert old == new
a = 10
a &= ~9
assert a == 2
