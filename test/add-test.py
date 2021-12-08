#!/usr/bin/env python
""" Trivial helper program to bytecompile and run an uncompile
"""
import os, sys, py_compile
from xdis.version_info import version_tuple_to_str

assert 2 <= len(sys.argv) <= 4
version = sys.version[0:3]
vers = sys.version_info[:2]
if sys.argv[1] in ("--run", "-r"):
    suffix = "_run"
    py_source = sys.argv[2:]
    i = 2
else:
    suffix = ""
    py_source = sys.argv[1:]
    i = 1
try:
    optimize = int(sys.argv[-1])
    py_source = sys.argv[i:-1]
except:
    optimize = 2

for path in py_source:
    short = os.path.basename(path)
    if short.endswith(".py"):
        short = short[: -len(".py")]
    if hasattr(sys, "pypy_version_info"):
        version = version_tuple_to_str(end=2, delimiter="")
        bytecode = f"bytecode_pypy{version}{suffix}/{short}py{version}.pyc"
    else:
        version = version_tuple_to_str(end=2)
        bytecode = f"bytecode_{version}{suffix}/{short}.pyc"

    print(f"byte-compiling {path} to {bytecode}")
    py_compile.compile(path, bytecode, optimize=optimize)
    os.system(f"../bin/decompyle3 -a -T {bytecode}")
