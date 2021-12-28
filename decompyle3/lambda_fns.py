#  Copyright (c) 2015-2016, 2818-2021 by Rocky Bernstein
#  Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
#  Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
#  Copyright (c) 1999 John Aycock
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
CPython magic- and version- independent disassembly routines

There are two reasons we can't use Python's built-in routines
from dis. First, the bytecode we are extracting may be from a different
version of Python (different magic number) than the version of Python
that is doing the extraction.

Second, we need structured instruction information for the
(de)-parsing step. Python 3.4 and up provides this, but we still do
want to run on earlier Python versions.
"""

import sys
from collections import deque

from xdis import check_object_path, iscode, load_module
from decompyle3.scanner import get_scanner
from decompyle3.semantics.pysource import code_deparse

# from spark_parser import GenericASTTraversal, DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG


def disco_deparse(version: str, co, out, is_pypy, debug_opts) -> None:
    """
    diassembles and deparses a given code block 'co'
    """

    assert iscode(co)

    # store final output stream for case of error
    real_out = out or sys.stdout
    print(f"# Python {version}", file=real_out)
    if co.co_filename:
        print(f"# Embedded file name: {co.co_filename}", file=real_out)

    scanner = get_scanner(version, is_pypy=is_pypy)

    queue = deque([co])
    disco_deparse_loop(scanner.ingest, queue, real_out, is_pypy, debug_opts)


def disco_deparse_loop(disasm, queue, real_out, is_pypy, debug_opts):
    while len(queue) > 0:
        co = queue.popleft()
        skip_token_scan = False
        if co.co_name == "<lambda>":
            print(
                "\n# %s line %d of %s"
                % (co.co_name, co.co_firstlineno, co.co_filename),
                file=real_out,
            )

            code_deparse(
                co,
                real_out,
                debug_opts=debug_opts,
                is_pypy=is_pypy,
                # compile_mode="exec",
                compile_mode="lambda",
            )
            skip_token_scan = True

        tokens, customize = disasm(co)
        if skip_token_scan:
            continue
        for t in tokens:
            if iscode(t.pattr):
                queue.append(t.pattr)
            elif iscode(t.attr):
                queue.append(t.attr)
            pass
        pass


PARSER_DEFAULT_DEBUG = {
    "rules": False,
    "transition": False,
    "reduce": True,
    "errorstack": "full",
    "context": True,
    "dups": False,
}


def decompile_lambda_fns(
    filename: str,
    outstream=None,
    showasm=None,
    showast={"after"},
    showgrammar=PARSER_DEFAULT_DEBUG,
) -> None:
    """
    decompile all of the lambda functions in a python byte-code file (.pyc)

    If given a Python source file (".py") file, we'll
    decompile all lambdas of the corresponding compiled object.
    """
    filename = check_object_path(filename)
    (version, timestamp, magic_int, co, is_pypy, source_size, sip_hash) = load_module(
        filename
    )

    debug_opts = {"asm": showasm, "ast": showast, "grammar": showgrammar}
    if type(co) == list:
        for con in co:
            disco_deparse(
                version, con, outstream, is_pypy, showasm, showast, showgrammar
            )
    else:
        disco_deparse(version, co, outstream, is_pypy, debug_opts)
    co = None


def _test() -> None:
    """Simple test program to disassemble a file."""
    argc = len(sys.argv)
    if argc != 2:
        if argc == 1:
            fn = __file__
        else:
            sys.stderr.write("usage: %s [-|CPython compiled file]\n" % __file__)
            sys.exit(2)
    else:
        fn = sys.argv[1]
    decompile_lambda_fns(fn)


if __name__ == "__main__":
    _test()
