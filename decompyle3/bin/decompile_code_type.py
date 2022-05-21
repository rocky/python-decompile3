#!/usr/bin/env python
# Mode: -*- python -*-
#
# Copyright (c) 2015-2016, 2018, 2020-2022 by Rocky Bernstein <rb@dustyfeet.com>
#
import click
import os
import sys

from xdis.version_info import version_tuple_to_str
from decompyle3.code_fns import (
    decompile_all_fragments,
    decompile_dict_comprehensions,
    decompile_generators,
    decompile_lambda_fns,
    decompile_list_comprehensions,
    decompile_set_comprehensions,
)
from decompyle3.main import decompile_file
from decompyle3.version import __version__

if click.__version__ >= "7.":
    case_sensitive = {"case_sensitive": False}
else:
    case_sensitive = {}

program, ext = os.path.splitext(os.path.basename(__file__))

PATTERNS = ("*.pyc", "*.pyo")


@click.command()
@click.option(
    "--format",
    "-F",
    "code_format",
    type=click.Choice(
        [
            "code-fragments",
            "dict-comprehension",
            "exec",
            "generator",
            "lambda",
            "list-comprehension",
            "set-comprehension",
        ],
        **case_sensitive,
    ),
)
@click.version_option(version=__version__)
@click.option("--asm/--no-asm", "-a", "show_asm", default=False)
@click.option("--grammar/--no-grammar", "-g", default=False)
@click.option("--tree/--no-tree", "-t", default=False)
@click.option("--tree++/--no-tree++", "-T", "tree_plus", default=False)
@click.option(
    "--output",
    "-o",
    "outfile",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=True, writable=True, resolve_path=True
    ),
    required=False,
)
@click.argument("files", nargs=-1, type=click.Path(readable=True), required=True)
def main(code_format, show_asm, grammar, tree, tree_plus, outfile, files):
    """Decompile all code objects of a certain format."""

    version_tuple = sys.version_info[0:2]
    if version_tuple not in ((3, 7), (3, 8),):
        print(
            f"Note: {program} can decompile only bytecode from Python 3.10"
            f"""\n\tYou have version: {version_tuple_to_str()}."""
        )

    # FIXME is there a "click" way to do this?
    if code_format is None:
        code_format = "lambda"

    if code_format == "code-fragments":
        decompile_fn = decompile_all_fragments
    elif code_format == "generator":
        decompile_fn = decompile_generators
    elif code_format == "lambda":
        decompile_fn = decompile_lambda_fns
    elif code_format == "dict-comprehension":
        decompile_fn = decompile_dict_comprehensions
    elif code_format == "list-comprehension":
        decompile_fn = decompile_list_comprehensions
    elif code_format == "set-comprehension":
        decompile_fn = decompile_set_comprehensions
    elif code_format == "exec":
        decompile_fn = decompile_file
    else:
        print(f"Unexpected code_format {code_format}")
        return 1

    # Use stdout if outfile is None
    if outfile is None:
        outfile = sys.stdout
    else:
        if os.path.isdir(outfile):
            outfile = None

    # maybe a second -a will do before as well
    asm = "after" if show_asm else None

    show_ast = {"before": tree, "after": tree_plus}
    show_grammar = {
        "rules": False,
        "transition": False,
        "reduce": grammar,
        "errorstack": "full",
        "context": True,
        "dups": False,
    }

    success = 0
    skipped = 0
    skipped = 0
    total = 0
    for filename in files:
        print(f"total: {total}, success: {success}")
        try:
            if os.path.isdir(filename):
                for subdir, dirs, files in os.walk(filename):
                    for filename in files:
                        filepath = subdir + os.sep + filename
                        if (
                            filepath.endswith(".pyc")
                            or filepath.endswith(".py")
                            or filepath.endswith(".pyo")
                        ):
                            succeeded = decompile_fn(
                                filepath,
                                outfile,
                                showasm=asm,
                                showgrammar=show_grammar,
                                showast=show_ast,
                            )
                            print()
                            if succeeded:
                                success += 1
                            elif succeeded is None:
                                skipped += 1
                            success += 1
                            total += 1
            elif os.path.exists(filename) and not os.path.islink(filename):
                if (
                    filename.endswith(".pyc")
                    or filename.endswith(".py")
                    or filename.endswith(".pyo")
                    or os.path.isdir(filename)
                ):
                    succeeded = decompile_fn(
                        filename,
                        outfile,
                        showasm=asm,
                        showgrammar=show_grammar,
                        showast=show_ast,
                    )
                    print()
                    if succeeded:
                        success += 1
                    elif succeeded is None:
                        skipped += 1
                    total += 1
            else:
                print(f"Can't read {filename}; skipping", file=outfile)
                skipped += 1
                total += 1
                pass
            pass
        # except RuntimeError:  # uncomment out and comment out below to see traceback
        except RuntimeError:
            print("Failure")
            print(sys.exc_info()[1])
            total += 1
        pass
    print(f"total: {total}, success: {success}, skipped: {skipped}")
    return


if __name__ == "__main__":
    main()
