# Bug in 3.6 was not taking "else" branch after compound "if"
# In earlier versions we had else detection needed here.

# RUNNABLE!
def f(a, b, c):
    if a and b:
        x = 1
    else:
        x = 2
    if c:
        x = 3
    return(x)

assert f(True, True, True) == 3
assert f(True, True, False) == 1
assert f(True, False, True) == 3
assert f(True, False, False) == 2

# From 3.7.7 test_strftime
# Bug was detecting nested if's in a loop
# And we also need to distiguish from "and"
def strftest(now, a, there, shape_t):
    for e in now:
        if a and e:
            shape_t += 3
        elif there:
                shape_t = 2
    return shape_t

assert strftest([False], True, True, 1) == 2
assert strftest([True], True, True, 1) == 4

def strftest2(now, a, there, shape_t):
    for e in now:
        if a:
            if e:
                shape_t += 3
        elif there:
                shape_t = 2
    return shape_t


assert strftest2([False], True, True, 1) == 1
assert strftest([True], True, True, 1) == 4
