# Issue 149
"This file is self checking"


def is_zero(a):
    keep_going = True
    while keep_going:
        try:
            5 / a
            keep_going = False
            x = False
        except:
            x = True
            keep_going = False
    return x


assert not is_zero(1)
assert is_zero(0)
