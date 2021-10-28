# https://github.com/rocky/python-decompile3/issues/67
# This is RUNNABLE!
r, w, e = ([], [], [])
if [] == r == w == e:
    r = [1]
assert r == [1]
