#!/usr/bin/env python
""" Trivial helper program to bytecompile and run an uncompile
"""
import os
import platform
import py_compile
import sys
from typing import List

import click
from xdis.version_info import version_tuple_to_str


@click.command()
@click.option(
    "--format",
    "-F",
    "code_format",
    type=click.Choice(
        [
            "dict-comprehension",
            "generator",
            "lambda",
            "list-comprehension",
            "set-comprehension",
            "exec",
            "run",
        ]
    ),
)
@click.option(
    "--asm++/--no-asm++",
    "-A",
    "asm_plus",
    default=False,
    help="show xdis assembler and tokenized assembler",
)
@click.option("--asm/--no-asm", "-a", "show_asm", default=False)
@click.option("--grammar/--no-grammar", "-g", default=False)
@click.option("--tree/--no-tree", "-t", default=False)
@click.option("--tree++/--no-tree++", "-T", "tree_plus", default=False)
@click.option("--optimize", "-O", default=-1)
@click.argument("files", nargs=-1, type=click.Path(readable=True), required=True)
def main(
    code_format,
    asm_plus: bool,
    show_asm: bool,
    grammar,
    tree: bool,
    tree_plus: bool,
    optimize,
    files: List[str],
):
    """Byte compile file and place it in the right category of testing bytecode."""

    assert 2 <= len(sys.argv) <= 4
    version = version_tuple_to_str(end=2, delimiter="")
    suffix = code_format
    decompile_opts = ""
    if show_asm:
        decompile_opts += " -a"
    if tree:
        decompile_opts += " -t"
    if tree_plus:
        decompile_opts += " -T"

    for path in files:
        short = os.path.basename(path)
        if short.endswith(".py"):
            short = short[: -len(".py")]
        version = version_tuple_to_str(end=2)
        pypy = "pypy" if platform.python_implementation() == "PyPy" else ""
        if suffix in ("exec", "run"):
            bytecode = f"bytecode_{version}{pypy}/{suffix}/{short}.pyc"
        else:
            bytecode = f"bytecode_{version}{pypy}/code-fragment/{suffix}/{short}.pyc"

        print(f"byte-compiling {path} to {bytecode}")
        py_compile.compile(path, bytecode, optimize=optimize)
        if code_format in ("exec", "run"):
            os.system(f"../bin/decompyle3 {decompile_opts} {bytecode}")
        else:
            os.system(
                f"../bin/decompyle-code -F {code_format} {decompile_opts} {bytecode}"
            )


if __name__ == "__main__":
    main()
