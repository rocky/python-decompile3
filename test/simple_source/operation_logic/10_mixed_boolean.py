# Self-checking test.
# Mixed boolean expresions

"""This program is self-checking!"""

b = True
assert b, "b = True"
c = False
assert not c, "c = False"
d = True

a = b and c or d
assert a, "b and c or d"
assert a  # Same thing without the message

a = (b or c) and d
assert a, "(b or c) and d"

a = b or c or d
assert a, "b or c or d"

a = b and c and d
assert not a, "b and c and d"

a = b or c and d
assert a, "b or c and d"
assert a  # Same thing without the message

a = b and (c or d)
assert a, "b and (c or d)"

a = b and c or d
assert a, "b and c or d"

a = (b or c and d) and b
assert a, "(b or c and d) and b)"

## This is different because we have b ... and b
# and code gets generated vary differently here
# a = (b or c and d or a) and b
# assert a
