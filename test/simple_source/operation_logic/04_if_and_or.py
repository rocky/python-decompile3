# 3.7+ is pretty complicated in changing the sense of test conditions for
# and/or and not adding UNARY_NOTs to handle Python source-code "not".
# The below is just a small example of the things we need to handle.

# Bug was in handling nor.
def or3(a, b, c, d):
    if a or b or c:
        d = 1
    else:
        d = 2
    return d

def nor3(a, b, c, d):
    if not (a or b or c):
        d = 1
    else:
        d = 2
    return d

# Bug was in getting mixed and/or's right.
def are_instructions_equal(a, b, c, d):
    return a and (b or c) and d

bool4 = (
    (True, True, True, True),
    (True, True, True, False),

    (True, True, False, True),
    (True, True, False, False),

    (True, False, True, True),
    (True, False, True, False),

    (True, False, False, True),
    (True, False, False, False),

    (False, True, True, True),
    (False, True, True, False),

    (False, True, False, True),
    (False, True, False, False),

    (False, False, True, True),
    (False, False, True, False),

    (False, False, False, True),
    (False, False, False, False),
    )

or3_expect = (1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2)

for i, t in enumerate(bool4):
    # print(or3(*t))
    got = or3(*t)
    assert got == or3_expect[i], f"got {got}, expect: {or3_expect[i]}"

for i, t in enumerate(bool4):
    # print(nor3(*t))
    got = nor3(*t)
    expect = 3 - or3_expect[i]
    assert got == expect, f"got {got}, expect: {expect}"

expects = (True, False, True, False, True, False, False, False,
          False, False, False, False, False, False, False, False)

for i, t in enumerate(bool4):
    got = are_instructions_equal(*t)
    # print(got)
    expect = expects[i]
    assert got == expect, f"got {got}, expect: {expect}"


# From 3.7.7 test_modulefinder.py
# Bug was detecting not turning "or" into nested "if"s
# inside a loop. nested "ifs" can't handle the "else"
# properly.
def create_package(source, a, b):
    for line in source:
        if a or b:
            x = 1
        else:
            x = 2
    return x

assert create_package([2], True, True)  == 1
assert create_package([2], True, False)  == 1
assert create_package([2], False, True)  == 1
assert create_package([2], False, False)  == 2
