# Just a few of the many control-flow bugs we've encountered.

# From 3.6.10 test_binascii.py
# Bug was getting "while c and noise" parsed correclty
# and not put into the "ifelsesmt"

# RUNNABLE!
def addnoise(c, noise):
    while c and noise:
        if c < 3:
            c = 2
        else:
            c = 3
        noise = False
    return c

assert addnoise(0, True) == 0
assert addnoise(1, False) == 1
assert addnoise(2, True) == 2
assert addnoise(3, True) == 3
assert addnoise(4, True) == 3
assert addnoise(5, False) == 5

# From 3.6.10 test_dbm_dumb.py
# Bug was getting attaching "else" to the right "if" in the
# presense of a loop.
def test_random(a, r):
    x = 0
    for dummy in r:
        if dummy:
            if a:
                x += 2
        else:
            x += 1
    return x

assert test_random(True, [1]) == 2
assert test_random(True, [1, 1]) == 4
assert test_random(False, [1]) == 0
assert test_random(False, [1, 1]) == 0

# From 2.7.17 test_frozen.py
# Bug was getting making sure we have "try" not
# "try"/"else"
def test_frozen(a, b):
    try:
        x = 1 / a
    except:
        x = 2

    try:
        x += 3 / b
    except:
        x += 4

    return x

assert test_frozen(1, 1) == 4.0
assert test_frozen(0, 1) == 5.0
assert test_frozen(0.5, 0) == 6.0
assert test_frozen(0, 0.5) == 8.0

# From 3.6.10 test_binop.py
# Bug was getting "other += 3" outside of "if"/"else.
def __floordiv__(a, b):
    other = 0
    if a:
        other = 1
    else:
        if not b:
            return 2
    other += 3
    return other

assert __floordiv__(True, True) == 4
assert __floordiv__(True, False) == 4
assert __floordiv__(False, True) == 3
assert __floordiv__(False, False) == 2

# From 3.7 test_complex
def assertFloatsAreIdentical(a, b):
    if a or b:
        if a and b:
            return True
    else:
        return False

assert assertFloatsAreIdentical(True, True) == True
assert assertFloatsAreIdentical(True, False) == None
assert assertFloatsAreIdentical(False, True) == None
assert assertFloatsAreIdentical(False, False) == False

# From 3.7.6 test_httplib.py
def _make_body(lines, a, b):
    x = 0
    for idx in lines:
        if idx and a:
            x = 1
        if b:
            x += 2
        else:
            x += 3
    return x

_make_body([True], True, True) == 3
_make_body([True], True, False) == 4
_make_body([True], False, True) == 2
_make_body([False], True, True) == 2
_make_body([False], True, False) == 3
_make_body([False], False, True) == 2
_make_body([False], False, False) == 3
