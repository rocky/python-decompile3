# Adapted from issue #40

"""This program is self-checking!"""
def is_valid(a):
    try:
        10 / a;
        return True
    except:
        return False

assert is_valid(1)
assert not is_valid(0)
