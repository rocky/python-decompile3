3.9.2
=====

* track xdis API changes
* bug fixes (many more remain)

3.9.1
=====

Lots of changes major changes. track xdis API changes.

Separate Phases more clearly:
* disassembly
* tokenization
* parsing
* abstracting to AST (more is done in newer projects)
* printing

Although we do not decompile bytecode greater than 3.8, code supports running from up to 3.12.

Many bugs fixed.

A lot of Linting and coding style modernization.

Work done in preparation for Blackhat Asia 2024

3.9.0
=====

* Speed up processing long literal collections: dictionary, list, set; we can also handle about 5K of them now
* Improve handling of async comprehensions: async "for"/"forelse", "async with"
* Reorganize semantic actions so that n_actions are separate; likewise for comprehensions and generators
* Improve 3.8 decompilation
* Support decompiling code fragment of comprehensions
* Correct various operator precedence, and show operator precedence in -T/--tree++
* Correct PyPy decompilation, support pyston-3.8-2.3.3
* Reorganize parsing modules and classes, to support fragment deparsing
* Add `BINARY_MATRIX_MULTPILY` in grammar
* Add pseudo opcode: LOAD_ARG; `JUMP_BACK` -> `JUMP_LOOP`; `MAKE_FUNCTION_8` -> `MAKE_FUNCTION_CLOSURE`
* Numerous bugs fixed, especially comprehension bugs
* Code cleanup
* Black format more files

3.8.0
=====

* Sync version number with corresponding uncompile6 version. The big change in 3.7.7 was using xdis >= 6.x
* use `expr_stmt` instead of `call_stmt` when that is what is meant
* remove float version tests
* better, but not perfect, `list .. if` comprehensions
* PyPy 3.8 testing support
* Start PyPy 3.7 and PyPy 3.8 decompilation support


3.7.7
=====

* Better handling of invalid bytecode magic
* Python 3.8 "try" with a "return" in "finally". Issue #67
* Support running from 3.9 and 3.10 although we do not support those bytecodes

3.7.6
=====

* Fix fragment comprehension bugs
* Makefile tolerance for pyston
* Revise for xdis 6.0.0 - in  Python version comparisons use tuples instead of floats

3.7.5
=====

Fix various bugs in fragment semantic actions. This mostly got stale with disuse, and make usable again now that it is used in trepan3k.


3.7.4
=====

First PyPI release. Version number is set to roughly the corresponding uncompyle6 version.
