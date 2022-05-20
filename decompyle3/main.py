# Copyright (C) 2018-2022 Rocky Bernstein <rocky@gnu.org>
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

import ast, datetime, py_compile, os, sys
import os.path as osp
import subprocess
import tempfile
from typing import Any, Optional, Tuple
from xdis import iscode, load_module
from xdis.version_info import (
    IS_PYPY,
    PYTHON_VERSION_TRIPLE,
    version_tuple_to_str,
)

from decompyle3.disas import check_object_path
from decompyle3.semantics import pysource
from decompyle3.parsers.parse_heads import ParserError
from decompyle3.version import __version__

# from decompyle3.linenumbers import line_number_mapping

from decompyle3.semantics.pysource import code_deparse, PARSER_DEFAULT_DEBUG
from decompyle3.semantics.fragments import code_deparse as code_deparse_fragments
from decompyle3.semantics.linemap import deparse_code_with_map


def _get_outstream(outfile: str) -> Any:
    dir = osp.dirname(outfile)
    failed_file = outfile + "_failed"
    if osp.exists(failed_file):
        os.remove(failed_file)
    try:
        os.makedirs(dir)
    except OSError:
        pass
    return open(outfile, mode="w", encoding="utf-8")


def syntax_check(filename: str) -> bool:
    with open(filename) as f:
        source = f.read()
    valid = True
    try:
        ast.parse(source)
    except SyntaxError:
        valid = False
    return valid


def decompile(
    co,
    bytecode_version: Tuple[int] = PYTHON_VERSION_TRIPLE,
    out=sys.stdout,
    showasm=None,
    showast={},
    timestamp=None,
    showgrammar=False,
    source_encoding=None,
    code_objects={},
    source_size=None,
    is_pypy=None,
    magic_int=None,
    mapstream=None,
    do_fragments=False,
    compile_mode="exec",
) -> Any:
    """
    ingests and deparses a given code block 'co'

    if `bytecode_version` is None, use the current Python intepreter
    version.

    Caller is responsible for closing `out` and `mapstream`
    """
    if bytecode_version is None:
        bytecode_version = PYTHON_VERSION_TRIPLE

    # store final output stream for case of error
    real_out = out or sys.stdout

    def write(s):
        s += "\n"
        real_out.write(s)

    assert iscode(co), f"""{co} does not smell like code"""

    co_pypy_str = "PyPy " if is_pypy else ""
    run_pypy_str = "PyPy " if IS_PYPY else ""
    sys_version_lines = sys.version.split("\n")
    if source_encoding:
        write("# -*- coding: %s -*-" % source_encoding)
    write(
        "# decompyle3 version %s\n"
        "# %sPython bytecode version base %s%s\n# Decompiled from: %sPython %s"
        % (
            __version__,
            co_pypy_str,
            version_tuple_to_str(bytecode_version),
            " (%s)" % str(magic_int) if magic_int else "",
            run_pypy_str,
            "\n# ".join(sys_version_lines),
        )
    )
    if co.co_filename:
        write("# Embedded file name: %s" % co.co_filename)
    if timestamp:
        write("# Compiled at: %s" % datetime.datetime.fromtimestamp(timestamp))
    if source_size:
        write("# Size of source mod 2**32: %d bytes" % source_size)

    # maybe a second -a will do before as well
    asm = "after" if showasm else None

    grammar = dict(PARSER_DEFAULT_DEBUG)
    if showgrammar:
        grammar["reduce"] = True
    debug_opts = {"asm": asm, "tree": showast, "grammar": grammar}

    try:
        if mapstream:
            if isinstance(mapstream, str):
                mapstream = _get_outstream(mapstream)

            deparsed = deparse_code_with_map(
                bytecode_version,
                co,
                out,
                showasm,
                showast,
                showgrammar,
                code_objects=code_objects,
                is_pypy=is_pypy,
            )
            header_count = 3 + len(sys_version_lines)
            linemap = [
                (line_no, deparsed.source_linemap[line_no] + header_count)
                for line_no in sorted(deparsed.source_linemap.keys())
            ]
            mapstream.write("\n\n# %s\n" % linemap)
        else:
            if do_fragments:
                deparse_fn = code_deparse_fragments
            else:
                deparse_fn = code_deparse
            deparsed = deparse_fn(
                co,
                out,
                bytecode_version,
                debug_opts=debug_opts,
                is_pypy=is_pypy,
                compile_mode=compile_mode,
            )
            pass
        return deparsed
    except pysource.SourceWalkerError as e:
        # deparsing failed
        raise pysource.SourceWalkerError(str(e))


def compile_file(source_path: str) -> str:
    if source_path.endswith(".py"):
        basename = source_path[:-3]
    else:
        basename = source_path

    if hasattr(sys, "pypy_version_info"):
        bytecode_path = "%s-pypy%s.pyc" % (basename, version_tuple_to_str())
    else:
        bytecode_path = "%s-%s.pyc" % (basename, version_tuple_to_str())

    print("compiling %s to %s" % (source_path, bytecode_path))
    py_compile.compile(source_path, bytecode_path, "exec")
    return bytecode_path


def decompile_file(
    filename: str,
    outstream=None,
    showasm=None,
    showast={},
    showgrammar=False,
    source_encoding=None,
    mapstream=None,
    do_fragments=False,
) -> Any:
    """
    decompile Python byte-code file (.pyc). Return objects to
    all of the deparsed objects found in `filename`.
    """

    filename = check_object_path(filename)
    code_objects = {}
    (version, timestamp, magic_int, co, is_pypy, source_size, sip_hash) = load_module(
        filename, code_objects
    )

    if isinstance(co, list):
        deparsed = []
        for bytecode in co:
            deparsed.append(
                decompile(
                    bytecode,
                    version,
                    outstream,
                    showasm,
                    showast,
                    timestamp,
                    showgrammar,
                    source_encoding,
                    code_objects=code_objects,
                    is_pypy=is_pypy,
                    magic_int=magic_int,
                    mapstream=mapstream,
                ),
            )
    else:
        deparsed = [
            decompile(
                co,
                version,
                outstream,
                showasm,
                showast,
                timestamp,
                showgrammar,
                source_encoding,
                code_objects=code_objects,
                source_size=source_size,
                is_pypy=is_pypy,
                magic_int=magic_int,
                mapstream=mapstream,
                do_fragments=do_fragments,
                compile_mode="exec",
            )
        ]
    co = None
    return deparsed


# FIXME: combine into an options parameter
def main(
    in_base: str,
    out_base: str,
    compiled_files: list,
    source_files: list,
    outfile=None,
    showasm=None,
    showast={},
    do_verify=Optional[str],
    showgrammar=False,
    source_encoding=None,
    raise_on_error=False,
    do_linemaps=False,
    do_fragments=False,
) -> Tuple[int, int, int, int]:
    """
    in_base	base directory for input files
    out_base	base directory for output files (ignored when
    files	list of filenames to be uncompyled (relative to in_base)
    outfile	write output to this filename (overwrites out_base)

    For redirecting output to
    - <filename>		outfile=<filename> (out_base is ignored)
    - files below out_base	out_base=...
    - stdout			out_base=None, outfile=None
    """
    tot_files = okay_files = failed_files = skipped = 0
    verify_failed_files = 0 if do_verify is not None else None
    current_outfile = outfile
    linemap_stream = None

    for source_path in source_files:
        compiled_files.append(compile_file(source_path))

    for filename in compiled_files:
        infile = osp.join(in_base, filename)
        # print("XXX", infile)
        if not osp.exists(infile):
            sys.stderr.write("File '%s' doesn't exist. Skipped\n" % infile)
            skipped += 1
            continue

        if do_linemaps:
            linemap_stream = infile + ".pymap"
            pass

        # print (infile, file=sys.stderr)

        if outfile:  # outfile was given as parameter
            outstream = _get_outstream(outfile)
        elif out_base is None:
            out_base = tempfile.mkdtemp(prefix="py-dis-")
            if do_verify and filename.endswith(".pyc"):
                current_outfile = osp.join(out_base, filename[0:-1])
                outstream = open(current_outfile, "w")
            else:
                outstream = sys.stdout
            if do_linemaps:
                linemap_stream = sys.stdout
        else:
            if filename.endswith(".pyc"):
                current_outfile = osp.join(out_base, filename[0:-1])
            else:
                current_outfile = osp.join(out_base, filename) + "_dis"
                pass
            pass

            outstream = _get_outstream(current_outfile)

        # print(current_outfile, file=sys.stderr)

        # Try to uncompile the input file
        try:
            deparsed_objects = decompile_file(
                infile,
                outstream,
                showasm,
                showast,
                showgrammar,
                source_encoding,
                linemap_stream,
                do_fragments,
            )
            if do_fragments:
                for deparsed_object in deparsed_objects:
                    last_mod = None
                    offsets = deparsed_object.offsets
                    for e in sorted(
                        [k for k in offsets.keys() if isinstance(k[1], int)]
                    ):
                        if e[0] != last_mod:
                            line = "=" * len(e[0])
                            outstream.write("%s\n%s\n%s\n" % (line, e[0], line))
                        last_mod = e[0]
                        info = offsets[e]
                        extractInfo = deparsed_object.extract_node_info(info)
                        outstream.write("%s" % info.node.format().strip() + "\n")
                        outstream.write(extractInfo.selectedLine + "\n")
                        outstream.write(extractInfo.markerLine + "\n\n")
                    pass
                pass
            if do_verify:
                for deparsed_object in deparsed_objects:
                    deparsed_object.f.close()
                    if PYTHON_VERSION_TRIPLE[:2] != deparsed_object.version[:2]:
                        sys.stdout.write(
                            f"\n# skipping running {deparsed_object.f.name} "
                            f"it is {version_tuple_to_str(deparsed_object.version, end=2)}, "
                            f"and we are {version_tuple_to_str(PYTHON_VERSION_TRIPLE, end=2)}\n"
                        )
                    else:
                        check_type = "syntax check"
                        if do_verify == "run":
                            check_type = "run"
                            result = subprocess.run(
                                [sys.executable, deparsed_object.f.name],
                                capture_output=True,
                            )
                            valid = result.returncode == 0
                            output = result.stdout.decode()
                            if output:
                                print(output)
                            pass
                            if not valid:
                                print(result.stderr.decode())

                        else:
                            valid = syntax_check(deparsed_object.f.name)

                        if not valid:
                            verify_failed_files += 1
                            sys.stderr.write(
                                f"\n# {check_type} failed on file {deparsed_object.f.name}\n"
                            )

                    # sys.stderr.write(f"Ran {deparsed_object.f.name}\n")
            tot_files += 1
        except (ValueError, SyntaxError, ParserError, pysource.SourceWalkerError) as e:
            sys.stdout.write("\n")
            sys.stderr.write(f"\n# file {infile}\n# {e}\n")
            failed_files += 1
            tot_files += 1
        except KeyboardInterrupt:
            if outfile:
                outstream.close()
                os.remove(outfile)
            sys.stdout.write("\n")
            sys.stderr.write(f"\nLast file: {infile}   ")
            raise
        except RuntimeError as e:
            sys.stdout.write(f"\n{str(e)}\n")
            if str(e).startswith("Unsupported Python"):
                sys.stdout.write("\n")
                sys.stderr.write(
                    "\n# Unsupported bytecode in file %s\n# %s\n" % (infile, e)
                )
            else:
                if outfile:
                    outstream.close()
                    os.remove(outfile)
                sys.stdout.write("\n")
                sys.stderr.write("\nLast file: %s   " % (infile))
                raise

        # except:
        #     failed_files += 1
        #     if current_outfile:
        #         outstream.close()
        #         os.rename(current_outfile, current_outfile + "_failed")
        #     else:
        #         sys.stderr.write("\n# %s" % sys.exc_info()[1])
        #         sys.stderr.write("\n# Can't uncompile %s\n" % infile)
        else:  # uncompile successful
            if current_outfile:
                outstream.close()
                okay_files += 1
                pass
            else:
                okay_files += 1
                if not current_outfile:
                    mess = "\n# okay decompiling"
                    # mem_usage = __memUsage()
                    print(mess, infile)
        if current_outfile:
            sys.stdout.write(
                "%s -- %s\r"
                % (
                    infile,
                    status_msg(
                        do_verify,
                        tot_files,
                        okay_files,
                        failed_files,
                        verify_failed_files,
                    ),
                )
            )
            try:
                # FIXME: Something is weird with Pypy here
                sys.stdout.flush()
            except Exception:
                pass
    if current_outfile:
        sys.stdout.write("\n")
        try:
            # FIXME: Something is weird with Pypy here
            sys.stdout.flush()
        except Exception:
            pass
        pass
    return (tot_files, okay_files, failed_files, verify_failed_files)


# ---- main ----

if sys.platform.startswith("linux") and os.uname()[2][:2] in ["2.", "3.", "4."]:

    def __memUsage():
        mi = open("/proc/self/stat", "r")
        mu = mi.readline().split()[22]
        mi.close()
        return int(mu) / 1000000


else:

    def __memUsage():
        return ""


def status_msg(
    do_verify: bool,
    tot_files: int,
    okay_files: int,
    failed_files: int,
    verify_failed_files: Optional[int],
):
    if tot_files == 1:
        if failed_files:
            return "\n# decompile failed"
        elif verify_failed_files:
            return "\n# decompile run verification failed"
        elif do_verify:
            return "\n# Successfully decompiled and ran or syntax-checked all files"
        else:
            return "\n# Successfully decompiled all files"
            pass
        pass
    mess = f"decompiled {tot_files} files: {okay_files} okay, {failed_files} failed"
    if do_verify:
        mess += f", {verify_failed_files} failed verification"
    return mess
