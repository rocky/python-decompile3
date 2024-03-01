#  Copyright (c) 2015-2016, 2818-2024 by Rocky Bernstein
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
from py_compile import PyCompileError
from typing import Optional

from xdis import check_object_path, iscode, load_module

from decompyle3.scanner import get_scanner
from decompyle3.semantics.pysource import (
    PARSER_DEFAULT_DEBUG,
    TREE_DEFAULT_DEBUG,
    code_deparse,
)


def disco_deparse(
    version: Optional[tuple],
    co,
    codename_map: dict,
    out,
    is_pypy,
    debug_opts,
    start_offset: int = 0,
    stop_offset: int = -1,
) -> None:
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
    disco_deparse_loop(
        version,
        scanner.ingest,
        codename_map,
        queue,
        real_out,
        is_pypy,
        debug_opts,
        start_offset=start_offset,
        stop_offset=stop_offset,
    )


def disco_deparse_loop(
    version: Optional[tuple],
    disasm,
    codename_map: dict,
    queue,
    real_out,
    is_pypy,
    debug_opts,
    start_offset: int = 0,
    stop_offset: int = -1,
):
    while len(queue) > 0:
        co = queue.popleft()
        skip_token_scan = False
        if co.co_name in codename_map:
            print(
                "\n# %s line %d of %s"
                % (co.co_name, co.co_firstlineno, co.co_filename),
                file=real_out,
            )

            code_deparse(
                co,
                real_out,
                version=version,
                debug_opts=debug_opts,
                is_pypy=is_pypy,
                compile_mode=codename_map[co.co_name],
                start_offset=start_offset,
                stop_offset=stop_offset,
            )
            skip_token_scan = True

        tokens, _ = disasm(co, show_asm=debug_opts.get("asm", None))
        if skip_token_scan:
            continue
        for t in tokens:
            if iscode(t.pattr):
                queue.append(t.pattr)
            elif iscode(t.attr):
                queue.append(t.attr)
            pass
        pass


def decompile_code_type(
    filename: str,
    codename_map: dict,
    outstream=None,
    showasm=None,
    showast=TREE_DEFAULT_DEBUG,
    showgrammar=PARSER_DEFAULT_DEBUG,
    start_offset=0,
    stop_offset=-1,
) -> bool:
    """
    decompile all lambda functions in a python byte-code file (.pyc)

    If given a Python source file (".py") file, we'll
    decompile all lambdas of the corresponding compiled object.
    """
    try:
        filename = check_object_path(filename)
    except (PyCompileError, ValueError) as e:
        print(f"Skipping {filename}:\n{e}")
        return False

    (version, _, _, co, is_pypy, _, _) = load_module(filename)

    # maybe a second -a will do before as well
    # asm = "after" if showasm else None

    debug_opts = {"asm": showasm, "tree": showast, "grammar": showgrammar}
    if isinstance(co, list):
        for bytecode in co:
            disco_deparse(
                version,
                bytecode,
                codename_map,
                outstream,
                is_pypy,
                debug_opts,
                start_offset=start_offset,
                stop_offset=stop_offset,
            )
    else:
        disco_deparse(
            version,
            co,
            codename_map,
            outstream,
            is_pypy,
            debug_opts,
            start_offset=start_offset,
            stop_offset=stop_offset,
        )
    return True


def decompile_dict_comprehensions(
    filename: str,
    outstream=None,
    showasm=None,
    showast=TREE_DEFAULT_DEBUG,
    showgrammar=PARSER_DEFAULT_DEBUG,
    start_offset: int = 0,
    stop_offset: int = -1,
) -> Optional[bool]:
    """
    decompile all the dictionary-comprehension functions in a python byte-code
    file (.pyc)

    If given a Python source file (".py") file, we'll
    decompile all dict_comprehensions of the corresponding compiled object.
    """
    return decompile_code_type(
        filename,
        {"<dictcomp>": "dictcomp"},
        outstream,
        showasm,
        showast,
        showgrammar,
        start_offset,
        stop_offset,
    )


def decompile_all_fragments(
    filename: str,
    outstream=None,
    showasm=None,
    showast=TREE_DEFAULT_DEBUG,
    showgrammar=PARSER_DEFAULT_DEBUG,
    start_offset: int = 0,
    stop_offset: int = -1,
) -> Optional[bool]:
    """
    decompile all comprehensions, generators, and lambda in a python byte-code
    file (.pyc)

    If given a Python source file (".py") file, we'll
    decompile all dict_comprehensions of the corresponding compiled object.
    """
    return decompile_code_type(
        filename,
        {
            "<dictcomp>": "dictcomp",
            "<genexpr>": "genexpr",
            "<lambda>": "lambda",
            "<listcomp>": "listcomp",
            "<setcomp>": "setcomp",
        },
        outstream,
        showasm,
        showast,
        showgrammar,
        start_offset=start_offset,
        stop_offset=stop_offset,
    )


def decompile_generators(
    filename: str,
    outstream=None,
    showasm=None,
    showast=TREE_DEFAULT_DEBUG,
    showgrammar=PARSER_DEFAULT_DEBUG,
    start_offset: int = 0,
    stop_offset: int = -1,
) -> Optional[bool]:
    """
    decompile all the generator functions in a python byte-code file (.pyc)

    If given a Python source file (".py") file, we'll
    decompile all dict_comprehensions of the corresponding compiled object.
    """
    return decompile_code_type(
        filename,
        {"<genexpr>": "genexpr"},
        outstream,
        showasm,
        showast,
        showgrammar,
        start_offset,
        stop_offset,
    )


def decompile_lambda_fns(
    filename: str,
    outstream=None,
    showasm=None,
    showast=TREE_DEFAULT_DEBUG,
    showgrammar=PARSER_DEFAULT_DEBUG,
    start_offset: int = 0,
    stop_offset: int = -1,
) -> Optional[bool]:
    """
    decompile all the lambda functions in a python byte-code file (.pyc)

    If given a Python source file (".py") file, we'll
    decompile all lambdas of the corresponding compiled object.
    """
    return decompile_code_type(
        filename,
        {"<lambda>": "lambda"},
        outstream,
        showasm,
        showast,
        showgrammar,
        start_offset=start_offset,
        stop_offset=stop_offset,
    )


def decompile_list_comprehensions(
    filename: str,
    outstream=None,
    showasm=None,
    showast=TREE_DEFAULT_DEBUG,
    showgrammar=PARSER_DEFAULT_DEBUG,
    start_offset: int = 0,
    stop_offset: int = -1,
) -> Optional[bool]:
    """
    decompile all of the lambda functions in a python byte-code file (.pyc)

    If given a Python source file (".py") file, we'll
    decompile all list_comprehensions of the corresponding compiled object.
    """
    return decompile_code_type(
        filename,
        {"<listcomp>": "listcomp"},
        outstream,
        showasm,
        showast,
        showgrammar,
        start_offset=start_offset,
        stop_offset=stop_offset,
    )


def decompile_set_comprehensions(
    filename: str,
    code_type,
    outstream=None,
    showasm=None,
    showast=TREE_DEFAULT_DEBUG,
    showgrammar=PARSER_DEFAULT_DEBUG,
    start_offset: int = 0,
    stop_offset: int = -1,
) -> Optional[bool]:
    """
    decompile all lambda functions in a python byte-code file (.pyc)

    If given a Python source file (".py") file, we'll
    decompile all list_comprehensions of the corresponding compiled object.
    """
    return decompile_code_type(
        filename,
        {"<setcomp>": "setcomp"},
        outstream,
        showasm,
        showast,
        showgrammar,
        start_offset=start_offset,
        stop_offset=stop_offset,
    )


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
    decompile_all_fragments(fn)


if __name__ == "__main__":
    _test()
