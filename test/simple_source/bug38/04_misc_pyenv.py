# From 3.8 test_ast.py
# Bug was in handling "withas" rule in 3.8
def test_invalid_sum(self):
    with f as cm:
        x = 1

def to_tuple(t):
    if t is None or isinstance(t, (str, int, complex)):
        return t

# From 3.8 _collections_abc.py
# Bug was "return" in nested for has two one for each loop)
#  ROT_TWO, POP_TOP
# combinations
def _check_methods(c, methods):
    for method in methods:
        for B in method:
            if c:
                return NotImplemented
            break

# Bug was handling the "return" at the end of the
# except. 3.8 has a fancy ROT_FOUR POP_EXCEPT for
# such a situation
def pop(self, key, default=__marker):
    try:
        value = 1
    except KeyError:
        if a:
            raise
        return default

# Another try/except problem where the except has a return in it.
def get(self, key, default=None):
    'D.get(k[,d]) -> D[k] if k in D, else d.  d defaults to None.'
    try:
        return self[key]
    except KeyError:
        return default

def setdefault(self, key, default=None):
    'D.setdefault(k[,d]) -> D.get(k,d), also set D[k]=d if k not in D'
    try:
        return self[key]
    except KeyError:
        self[key] = default
    return default
