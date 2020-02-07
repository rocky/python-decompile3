# From 3.7 _pyio.py
# Bug was handling multiple "or"s in an "if" in 3.7

# RUNNABLE!
def pyio_open(a, b, c, d):
    if a or b or c or d:
        raise

def pyio_open2(creating, writing, appending):

    if creating or writing or appending:
        x = 1
    else:
        x = 2
    return x

assert pyio_open2(True, False, False) == 1
assert pyio_open2(False, False, False) == 2


def identity(x):
    return x
pyio_open(False, False, False, False)
assert identity(1) and 0 == False
assert identity(1) or 0 == True
