# 2.6.9 calendar.py
# Bug in 2.6.9 was handling with as. Added rules

#
#       withasstmt ::= expr setupwithas store suite_stmts_opt
#                      POP_BLOCK LOAD_CONST COME_FROM WITH_CLEANUP END_FINALLY
#       setupwithas ::= DUP_TOP LOAD_ATTR ROT_TWO LOAD_ATTR CALL_FUNCTION_0 STORE_FAST
#                       SETUP_FINALLY LOAD_FAST DELETE_FAST

def formatweekday(self):
    with self as encoding:
        return encoding

# Bug in 2.7.14 test_contextlib.py. Bug was not enclosing (x,y) in parenthesis
def withas_bug(self, nested, a, b):
    with self.assertRaises(ZeroDivisionError):
        with nested(a(), b()) as (x, y):
                1 // 0

# From 3.7.7 test_functools.py
# Bug is a unreachable code after "return"
def test_invalid_registrations(x):
    return
    with x:
        x = 1

# From 3.7.7 test_re.py
# Bug was hooking in c_with.
def test_re_tests(tests):
    for t in tests:
        with a:
            continue
