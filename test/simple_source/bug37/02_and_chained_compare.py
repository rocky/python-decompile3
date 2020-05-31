# In Python 3.7+ and/or's have gotten a lot smarter and are harder to
# deal with.

# See:
# https://github.com/rocky/python-uncompyle6/issues/317

"""This program is self-checking!"""

def chained_compare_and(a, b):
	assert (0 <= a <= 10 and
		10 <= b <= 20)
	return 6

assert chained_compare_and(5, 15) == 6
try:
    chained_compare_and(13, 16)
except:
    pass
else:
    raise


try:
    chained_compare_and(4, 8)
except:
    pass
else:
    raise
