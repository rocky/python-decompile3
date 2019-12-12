# from 3.7 inspect.py
# Bug was "if not predicate or" inside "for".
# Jump optimization turns a POP_JUMP_IF_TRUE into
# a POP_JUMP_IF_FALSE and this has to be
# dealt with at the "if" (or actually "testfalse") level.

# RUNNABLE!
def getmembers(names, object, predicate):
    for key in names:
        if not predicate or object:
            object = 2
        object += 1
    return object

assert getmembers([1], 0, False) == 3
assert getmembers([1], 1, True) == 3
assert getmembers([1], 0, True) == 1
assert getmembers([1], 1, False) == 3
assert getmembers([], 1, False) == 1
assert getmembers([], 2, True) == 2
