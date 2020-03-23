# From Python 3.7 pickle.py
# Bug was different code generation for chained comparisons than prior Python versions

# RUNNABLE!
def chained_compare_a(protocol):
    if not 0 <= protocol <= 7:
        raise ValueError("pickle protocol must be <= %d" % 7)


def chained_compare_b(a, obj):
    if a:
        if -0x80000000 <= obj <= 0x7fffffff:
            return 1

def chained_compare_c(a, d):
    for i in range(len(d)):
        if a == d[i] != 2:
            return 5

# From uncompyle6 python24.py
# 3.7 bug was in detecting "if" chained compare inside another "if"
def reduce_is_invalid(a, b, c):
    if a:
        if 0 <= b < 5:
            return 2
    elif c:
        return 5

chained_compare_a(3)
try:
    chained_compare_a(8)
except ValueError:
    pass

assert chained_compare_b(True, 0x0) == 1
assert chained_compare_c(3, [3]) == 5
assert chained_compare_c(2, [2]) is None
assert reduce_is_invalid(False, 1, True) == 5
assert reduce_is_invalid(True, 1, True) == 2
assert reduce_is_invalid(True, 10, True) is None
assert reduce_is_invalid(True, -1, True) is None

# Bug is chained comparison of more than two operators
if 0 < 1 <= 1 == 1 >= 1 > 0 != 1:
    pass
else:
    assert False

# From 3.7 test_tcl.py
# Bug was "or" with a chained compare. We needed
# to limit the scope of iflaststmt because that
# reduction was hiding the possibility of chained-compare
# reductions. Reductions in grammar rules can prevent
# others from occurring that might have triggered
# otherwise.
def get_integers(a, b):
    integers = 1
    if (a or
        8 <=
        b
        < 10):
        integers = 2
    return integers

assert get_integers(True, 0) == 2
assert get_integers(False, 0) == 1
assert get_integers(False, 20) == 1
assert get_integers(False, 8) == 2
assert get_integers(False, 9) == 2
