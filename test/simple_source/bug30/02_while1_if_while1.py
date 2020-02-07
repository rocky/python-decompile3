# From python 3.4 sre.pyc
while 1:
    if __file__:
        while 1:
            if __file__:
                break
            raise RuntimeError
    else:
        raise RuntimeError

# From 3.7.6 test_generators.py
# Bug was confusing inner "while/else" with "while"
# Note that there is a condition test immidiately after the outer while1.
def flat_conjoin(i):
    while 1:
        while i >= 0:
            i -= 1
        else:
            assert i
            break
