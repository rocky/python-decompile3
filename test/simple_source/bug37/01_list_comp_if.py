"""This program is self-checking!"""
items = [True, False, True]
control = True

# We use weird line breaks to assist in
# checkint decompilation correspondences
# fmt: off
result = [
    item
    for item
    in items
    if item or
    control]
# fmt: on

# Python compilation on 3.7 and 3.8 seems to remove "assert" statements?
# So we'll use an "if" instead of an "assert"
if result != [True, False, True]:
    raise RuntimeError("list comprehension with 'a and b'")

# fmt: off
result = [
    item
    for item
    in items
    if item or not control]
# fmt: on

if result != [True, True]:
    raise RuntimeError("list comprehension with 'a and not b'")


# This is adapted from 3.7.6 decimal.py where
# what we really have is ... "if a or not b" which
# is a different condition.

# At the time of writing this we don't decompile that correctly and this needs fixing
# However we were *also* adding an additional "if" at the end.
# The below checks this part of it.
# We also note the unpyc37 gets this wrong too while pycdc SEGVs
a, b = False, False

# fmt: off
x = [
    s
    for s
    in __file__
    if not a
    if not b]
# fmt: on

assert "".join(x) == __file__
a, b = True, True

# fmt: off
x = [s
     for s
     in __file__
     if not a
     if not b]
# fmt: on

assert x == []
