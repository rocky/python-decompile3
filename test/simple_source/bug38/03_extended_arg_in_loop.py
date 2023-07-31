# Bug is code with extended arg and misdetecting loop ends.
"""This program is self checking"""

# fmt: off
shape_t = [
    0, 1, 2, 3, 5, 6, 7, 8, 9,
    11, 1, 2, 3, 5, 6, 7, 8, 9,
    21, 1, 2, 3, 5, 6, 7, 8, 9,
    31, 1, 2, 3, 5, 6, 7, 8, 9,
    41, 1, 2, 3, 5, 6, 7, 8, 9,
    51, 1, 2, 3, 5, 6, 7, 8, 9,
    61, 1, 2, 3, 5, 6, 7, 8, 9,
    71, 1, 2, 3, 5, 6, 7, 8, 9,
    81, 1, 2, 3, 5, 6, 7, 8, 9,
    91, 1, 2, 3, 5, 6, 7, 8, 9,
    101, 1, 2, 3, 5, 6, 7, 8, 9,
    111, 1, 2, 3, 5, 6, 7, 8, 9,
    121, 1, 2, 3, 5, 6, 7, 8, 129,
]

if shape_t[0] != 0:
    for profile in enumerate(shape_t):
        mainstart = 5
    assert False
else:
    assert True
