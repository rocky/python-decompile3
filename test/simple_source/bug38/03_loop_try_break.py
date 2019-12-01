# From uncompyle issue #295 on 3.8
# In 3.8 BREAK_LOOP and CONTINUE_LOOP no longer exist.
# The bug is that the "break" is turned into:
# POP_BLOCK
# JUMP_ABSOLUTE
while True:
    try:
        x = 1
        break
    except Exception:
        pass

while True:
    try:
        x -= 1
    except Exception:
        break

# Issue #25 https://github.com/rocky/python-decompile3/issues/25
# Same as above using "for".
for i in range(5):
    try:
        x = 1
        break
    except Exception:
        if i == 4:
            raise
