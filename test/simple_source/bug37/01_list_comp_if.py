items = [True, False, True]
control = True
result = [item for item in items if (item or control)]

# Python compilation on 3.7 and 3.8 seems to remove "assert" statements?
# So we'll use an "if" instead of an "assert"
if result != [True, False, True]:
    raise RuntimeError("list comprehension with 'a and b'")

result = [item for item in items if (item or not control)]

if result != [True, True]:
    raise RuntimeError("list comprehension with 'a and not b'")
