# 2.6.9 _strptime.py
# In 2.6 bug in handling BREAK_LOOP followed by JUMP_LOOP
# So added rule:
#  break_stmt ::= BREAK_LOOP JUMP_LOOP
for value in __file__:
    if value:
        if value and __name__:
            pass
        else:
            tz = "a"
            break
