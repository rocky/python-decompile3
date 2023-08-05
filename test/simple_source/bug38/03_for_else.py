# Test bugs in detecting for/else vs for.
"This file is self checking"


def for_test_with_break(items):
    x = a = 10
    for a in items:
        x = a
        break
    if x != 10:
        x = 20
    return x


def for_test_without_break():
    x = a = 10
    for a in []:
        x = a
    if x != 10:
        x = 20
    return x


def forelse_test_with_break(items):
    x = a = 30
    for a in items:
        x = a
        break
    else:
        if x != 30:
            x = 20
        return x


def forelse_test_without_break():
    'for/else here is equivalent to "for"'
    x = a = 10
    # When there is no "break" in a "for/else"
    # loop it is the same as a "for" loop.
    #  So this will get turned into a "for".
    for a in []:
        x = a
    else:
        if x != 10:
            x = 20
        return x


assert for_test_with_break([]) == 10
assert for_test_with_break([1]) == 20
assert forelse_test_with_break([]) == 30
assert forelse_test_with_break([1]) is None
