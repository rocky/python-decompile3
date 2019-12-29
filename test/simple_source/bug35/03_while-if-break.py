# Python 3.5 and 3.6 break inside a
# while True and if / break

def display_date(loop):
    while True:
        if loop:
            break
        x = 5

    # Another loop to test 3.5 ifelsestmtl grammar rule
    while loop:
        if x:
            True
        else:
            True

# RUNNABLE!
def print_super_classes3(kwargs, i):
    if kwargs:
        while i:
            i -= 1
    else:
        i = 2
    return i

assert print_super_classes3(False, 3) == 2
assert print_super_classes3(True, 3) == 0
