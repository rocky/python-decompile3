# From 3.7 _pyio.py
# Bug was handling multiple "or"s in an "if" in 3.7

# RUNNABLE!
def pyio_open(a, b, c, d):
    if a or b or c or d:
        raise

def identity(x):
    return x
pyio_open(False, False, False, False)
assert identity(1) and 0 == False
assert identity(1) or 0 == True
