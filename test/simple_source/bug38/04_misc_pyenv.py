# From 3.8 test_ast.py
# Bug was in handling "withas" rule in 3.8
def test_invalid_sum(self):
    with f as cm:
        x = 1

def to_tuple(t):
    if t is None or isinstance(t, (str, int, complex)):
        return t

# From 3.8 abc.py
# Bug was "return" in nested for has two one for each loop)
#  ROT_TWO, POP_TOP
# combinations
def _check_methods(c, methods):
    for method in methods:
        for B in method:
            if c:
                return NotImplemented
            break
