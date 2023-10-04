# These are adapted from generators found when byte compiling the
# entire set of 3.8 installed packages on my disk.
# Many examples come from packages like sympy or numpy

# fmt: off
# generator bugs
(i
 for i
 in
 range(10)
 )

tuple(j
       for j
       in t
       if i != j)

# # 3.8.12 weakrefset.py
# (e
#  for s
#  in ("a", "b")
#  for e
#  in s)

# # Python 3.8.2 line 683 of git/refs/symbolic.py
# # Bug was in handling "or not"
# (r
#  for r
#  in (0, 1, 2, 3)
#  if r
#  or
#  not
#  5 % 2)

# # line 1512 of sympy/core/mul.py
# # Bug was handling "and"
# (x
#   and
#   (x + 1 % 2)
#  is True for
#  x
#  in (0, 1, 2)
#  )

# # line 330 of 3.8.12 setuptools/config.py
# # Problem was in handling or True
# (
#  path
#  for path in __file__
#  if (path or True))

# # Line 602 of 3.8.2 nltk/corpus/reader/framenet.py
# # Bug was handling looping jump of chained comparison inside comp_if.
# (1
#  for x,
#  y
#  in __file__
#  if 2 <= y
#  < 3
#  or 5
#  <= x
#  < 6)

# # The problem was handing IfExp as part of a tuple, i.e.
# #  (None if .. and .. else)
# (
#  (k,
#   (None if
#    k
#    and v
#    else v)
#    )
#  for k, v in
#  {"foo": "bar"}
#  )

# # line 1086 of 3.8.12 test/test_asyncgen.py
# # Bug was hooking genexpr_func_async to return_expr_lambda in grammar
# # and writing a semantic action for this when the code is decompiled
# # independant of the calling context.
# (i * 2
#  async
#  for i
#  in range(10))
