|buildstatus| |Latest Version| |Supported Python Versions|

decompyle3
==========

A native Python cross-version decompiler and fragment decompiler.
A reworking of uncompyle6_.


Introduction
------------

*decompyle3* translates Python bytecode back into equivalent Python
source code. It accepts bytecodes from Python version 3.7 on.

For decompilation of older Python bytecode see uncompyle6_.

Why this?
---------

Uncompyle6 is awesome, but it has has a fundamental problem in the way
it handles control flow. In the early days of Python when there was
little optimization and code was generated in a very template-oriented
way, code generation could be done by simply looking at code patterns.

Over the years more code optimization, specifically around handling
jumps has made it harder to support detecting control flow strictly
from code patterns. This was noticed as far back as Python 2.4 (2004)
but since this is a difficult problem, so far it hasn't been tackled.

The initial fix to this to add markers in the instruction stream,
initially this was a `COME_FROM` instruction, and then use that in
pattern detection.

Over the years, I've extended that to be more specific, so
`COME_FROM_LOOP` and `COME_FROM_WITH` were added. And I added checks
at grammar reduce type to make try to make sure jumps match with
supposed `COME_FROM` targets.

However all of this is complicated, not robust, and not really tenable.

So in this project we'll address control flow directly via
the python-control-flow_ project.

I expect it will be a while before this is as good as *uncompyle6* for
Python 3.7, but if decompilation is to have a future in Python, this
work is necessary.


Requirements
------------

The code here can be run on Python versions 3.7 or later. The bytecode
files it can read have been tested on Python bytecodes from versions
3.7 and later.

Installation
------------

This uses setup.py, so it follows the standard Python routine:

::

    pip install -e .  # set up to run from source tree
                      # Or if you want to install instead
    python setup.py install # may need sudo

A GNU makefile is also provided so :code:`make install` (possibly as root or
sudo) will do the steps above.

Testing
-------

::

   make check

A GNU makefile has been added to smooth over setting running the right
command, and running tests from fastest to slowest.

If you have remake_ installed, you can see the list of all tasks
including tests via :code:`remake --tasks`


Usage
-----

Run

::

$ decompyle3 *compiled-python-file-pyc-or-pyo*

For usage help:

::

   $ decompyle3 -h

If you want strong verification of the correctness of the
decompilation process, add the `--verify` option. But there are
situations where this will indicate a failure, although the generated
program is semantically equivalent. Using option `--weak-verify` will
tell you if there is something definitely wrong. Generally, large
swaths of code are decompiled correctly, if not the entire program.

You can also cross compare the results with pycdc_ . Since they work
differently, bugs here often aren't in that, and vice versa.

Also check against uncompyle6_.


Known Bugs/Restrictions
-----------------------

The verification checks to see if the resulting decompiled source
is a valid Python program by running the Python interpreter. Because
the Python language has changed so much, for best results you should
use the same Python version in checking as was used in creating the
bytecode.

There are however an interesting class of these programs that is
readily available give stronger verification: those programs that
when run check some computation, or even better themselves.

And already Python has a set of programs like this: the test suite
for the standard library that comes with Python. We have some
code in `test/stdlib` to facilitate this kind of checking.

**We support only released versions, not candidate versions.** Note however
that the magic of a released version is usually the same as the *last* candidate version prior to release.

We also don't handle PJOrion_ obfuscated code. For that try: PJOrion
Deobfuscator_ to unscramble the bytecode to get valid bytecode before
trying this tool. This program can't decompile Microsoft Windows EXE
files created by Py2EXE_, although we can probably decompile the code
after you extract the bytecode properly. For situations like this, you
might want to consider a decompilation service like `Crazy Compilers
<http://www.crazy-compilers.com/decompyle/>`_.  Handling
pathologically long lists of expressions or statements is slow.


There is lots to do, so please dig in and help.

See Also
--------

* https://github.com/zrax/pycdc : purports to support all versions of Python. It is written in C++ and is most accurate for Python versions around 2.7 and 3.3 when the code was more actively developed. Accuracy for more recent versions of Python 3 and early versions of Python are especially lacking. See its `issue tracker <https://github.com/zrax/pycdc/issues>`_ for details. Currently lightly maintained.
* https://code.google.com/archive/p/unpyc3/ : supports Python 3.2 only. The above projects use a different decompiling technique than what is used here. Currently unmaintained.
* https://github.com/figment/unpyc3/ : fork of above, but supports Python 3.3 only. Includes some fixes like supporting function annotations. Currently unmaintained.
* https://github.com/wibiti/uncompyle2 : supports Python 2.7 only, but does that fairly well. There are situations where `decompyle3` results are incorrect while `uncompyle2` results are not, but more often decompyle3 is correct when uncompyle2 is not. Because `decompyle3` adheres to accuracy over idiomatic Python, `uncompyle2` can produce more natural-looking code when it is correct. Currently `uncompyle2` is lightly maintained. See its issue `tracker <https://github.com/wibiti/uncompyle2/issues>`_ for more details
* `How to report a bug <https://github.com/rocky/python-decompile3/blob/master/HOW-TO-REPORT-A-BUG.md>`_
* The HISTORY_ file.
* https://github.com/rocky/python-xdis : Cross Python version disassembler
* https://github.com/rocky/python-xasm : Cross Python version assembler
* https://github.com/rocky/python-decompile3/wiki : Wiki Documents which describe the code and aspects of it in more detail


.. _uncompyle6: https://pypi.python.org/pypi/uncompyle6
.. _python-control-flow: https://github.com/rocky/python-control-flow
.. _trepan: https://pypi.python.org/pypi/trepan2
.. _compiler: https://pypi.python.org/pypi/spark_parser
.. _HISTORY: https://github.com/rocky/python-decompile3/blob/master/HISTORY.md
.. _debuggers: https://pypi.python.org/pypi/trepan3k
.. _remake: https://bashdb.sf.net/remake
.. _pycdc: https://github.com/zrax/pycdc
.. _this: https://github.com/rocky/python-decompile3/wiki/Deparsing-technology-and-its-use-in-exact-location-reporting
.. |buildstatus| image:: https://travis-ci.org/rocky/python-decompile3.svg
		 :target: https://travis-ci.org/rocky/python-decompile3
.. _PJOrion: http://www.koreanrandom.com/forum/topic/15280-pjorion-%D1%80%D0%B5%D0%B4%D0%B0%D0%BA%D1%82%D0%B8%D1%80%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5-%D0%BA%D0%BE%D0%BC%D0%BF%D0%B8%D0%BB%D1%8F%D1%86%D0%B8%D1%8F-%D0%B4%D0%B5%D0%BA%D0%BE%D0%BC%D0%BF%D0%B8%D0%BB%D1%8F%D1%86%D0%B8%D1%8F-%D0%BE%D0%B1%D1%84
.. _Deobfuscator: https://github.com/extremecoders-re/PjOrion-Deobfuscator
.. _Py2EXE: https://en.wikipedia.org/wiki/Py2exe
.. |Supported Python Versions| image:: https://img.shields.io/pypi/pyversions/decompyle3.svg
.. |Latest Version| image:: https://badge.fury.io/py/decompyle3.svg
		 :target: https://badge.fury.io/py/decompyle3
