#!/usr/bin/env python
# emacs-mode: -*-python-*-

"""
test_pythonlib.py -- compile, decompile, and verify Python libraries

Usage-Examples:

  # decompile, and verify the first 100 python 3.7 byte-compiled files
  test_pythonlib.py --3.7 --syntax-verify

  # Same as above longer decompile up to 2100
  test_pythonlib.py --3.7 --syntax-verify --max=2100

  # Same as above but compile the base set first
  test_pythonlib.py --3.7 --syntax-verify --max=2100 --compile

Adding own test-trees:

Step 1) Edit this file and add a new entry to 'test_options', eg.
  test_options['mylib'] = ('/usr/lib/mylib', PYOC, 'mylib')
Step 2: Run the test:
  test_pythonlib.py --mylib	  # decompile 'mylib'
  test_pythonlib.py --mylib --syntax-verify # decompile verify 'mylib'
"""

import getopt
import os
import py_compile
import shutil
import sys
import tempfile
import time
from fnmatch import fnmatch

from xdis.version_info import version_tuple_to_str

from decompyle3.main import main


def get_srcdir():
    filename = os.path.normcase(os.path.dirname(__file__))
    return os.path.realpath(filename)


src_dir = get_srcdir()


# ----- configure this for your needs

lib_prefix = "/usr/lib"
# lib_prefix = [src_dir, '/usr/lib/', '/usr/local/lib/']

target_base = tempfile.mkdtemp(prefix="py-dis-")

PY = ("*.py",)
PYC = ("*.pyc",)
PYO = ("*.pyo",)
PYOC = ("*.pyc", "*.pyo")

test_options = {
    # name:   (src_basedir, pattern, output_base_suffix, python_version)
    "test": ("test", PYC, "test"),
}

for vers in ("3.7", "3.8", "3.8pypy"):
    bytecode = "bytecode_%s" % vers
    key = "bytecode-%s" % vers
    test_options[key] = (bytecode, PYC, bytecode, vers)
    bytecode = "bytecode_%s_run" % vers
    key = "bytecode-%s/run" % vers
    test_options[key] = (bytecode, PYC, bytecode, vers)
    key = "%s" % vers
    pythonlib = "python%s" % vers
    if isinstance(vers, float) and vers >= 3.0:
        pythonlib = os.path.join(pythonlib, "__pycache__")
    test_options[key] = (os.path.join(lib_prefix, pythonlib), PYOC, pythonlib, vers)

vers = 3.7
bytecode = "bytecode_pypy%s_run" % vers
key = "bytecode-pypy37"
test_options[key] = (bytecode, PYC, bytecode, vers)


# -----


def help():
    print(
        """Usage-Examples:

  # compile, decompyle and verify short tests for Python 3.7:
  test_pythonlib.py --bytecode-3.7 --syntax-verify --compile

  # decompile all of Python's installed lib files
  test_pythonlib.py --3.7
"""
    )
    sys.exit(1)


def do_tests(src_dir, obj_patterns, target_dir, opts):
    def file_matches(files, root, basenames, patterns):
        files.extend(
            [
                os.path.normpath(os.path.join(root, n))
                for n in basenames
                for pat in patterns
                if fnmatch(n, pat)
            ]
        )

    files = []

    if opts["compile_type"] == "lambda":
        src_dir += "/code-fragment/lambda"
    elif opts["compile_type"] == "dict-comprehension":
        src_dir += "/code-fragment/dict-comprehension"
    elif opts["compile_type"] == "list-comprehension":
        src_dir += "/code-fragment/list-comprehension"
    elif opts["compile_type"] == "set-comprehension":
        src_dir += "/code-fragment/set-comprehension"
    elif opts["compile_type"] == "run":
        src_dir += "/run"
    else:
        src_dir += "/exec"

    # Change directories so use relative rather than
    # absolute paths. This speeds up things, and allows
    # main() to write to a relative-path destination.
    cwd = os.getcwd()
    os.chdir(src_dir)

    if opts["do_compile"]:
        compiled_version = opts["compiled_version"]
        if compiled_version and version_tuple_to_str() != compiled_version:
            print(
                "Not compiling: desired Python version is %s but we are running %s"
                % (compiled_version, version_tuple_to_str()),
                file=sys.stderr,
            )
        else:
            for root, dirs, basenames in os.walk(src_dir):
                file_matches(files, root, basenames, PY)
                for sfile in files:
                    py_compile.compile(sfile)
                    pass
                pass
            files = []
            pass
        pass

    for root, dirs, basenames in os.walk("."):
        # Turn root into a relative path
        dirname = root[2:]  # 2 = len('.') + 1
        file_matches(files, dirname, basenames, obj_patterns)

    if not files:
        print(
            "Didn't come up with any files to test! Try with --compile?",
            file=sys.stderr,
        )
        exit(1)

    os.chdir(cwd)
    files.sort()

    if opts["start_with"]:
        try:
            start_with = files.index(opts["start_with"])
            files = files[start_with:]
            print(">>> starting with file", files[0])
        except ValueError:
            pass

    print(time.ctime())
    print("Source directory: ", src_dir)
    print("Output directory: ", target_dir)
    try:
        _, _, failed_files, failed_verify = main(
            in_base=src_dir,
            out_base=target_dir,
            compiled_files=files,
            source_files=[],
            do_verify=opts["do_verify"],
        )
        if failed_files != 0:
            sys.exit(2)
        elif failed_verify:
            parent_dir = os.path.dirname(target_dir)
            print("Verify failed, keeping %s" % parent_dir)
            sys.exit(3)

    except (KeyboardInterrupt, OSError):
        print()
        sys.exit(1)
    if test_opts["rmtree"]:
        parent_dir = os.path.dirname(target_dir)
        print("Everything good, removing %s" % parent_dir)
        shutil.rmtree(parent_dir)


if __name__ == "__main__":
    test_dirs = []
    checked_dirs = []
    start_with = None

    test_options_keys = list(test_options.keys())
    test_options_keys.sort()
    opts, args = getopt.getopt(
        sys.argv[1:],
        "",
        [
            "start-with=",
            "verify-run",
            "syntax-verify",
            "all",
            "dict-comprehension",
            "generator",
            "lambda",
            "list-comprehension",
            "set-comprehension",
            "compile",
            "coverage",
            "no-rm",
            "run",
        ]
        + test_options_keys,
    )
    if not opts:
        help()

    test_opts = {
        "do_compile": False,
        "do_verify": None,
        "start_with": None,
        "rmtree": True,
        "coverage": False,
        "compile_type": "exec",
    }

    for opt, val in opts:
        if opt == "--syntax-verify":
            test_opts["do_verify"] = "weak"
        elif opt == "--verify-run":
            test_opts["do_verify"] = "verify-run"
        elif opt == "--compile":
            test_opts["do_compile"] = True
        elif opt == "--lambda":
            test_opts["compile_type"] = "lambda"
        elif opt == "--dict-comprehension":
            test_opts["compile_type"] = "dict-comprehension"
        elif opt == "--generator":
            test_opts["compile_type"] = "generator"
        elif opt == "--list-comprehension":
            test_opts["compile_type"] = "list-comprehension"
        elif opt == "--run":
            test_opts["compile_type"] = "run"
        elif opt == "--set-comprehension":
            test_opts["compile_type"] = "set-comprehension"
        elif opt == "--start-with":
            test_opts["start_with"] = val
        elif opt == "--no-rm":
            test_opts["rmtree"] = False
        elif opt[2:] in test_options_keys:
            test_dirs.append(test_options[opt[2:]])
        elif opt == "--all":
            for val in test_options_keys:
                test_dirs.append(test_options[val])
        elif opt == "--coverage":
            test_opts["coverage"] = True
        else:
            help()
            pass
        pass

    if test_opts["coverage"]:
        os.environ["SPARK_PARSER_COVERAGE"] = (
            "/tmp/spark-grammar-python-lib%s.cover" % test_dirs[0][-1]
        )

    last_compile_version = None
    for src_dir, pattern, target_dir, compiled_version in test_dirs:
        if os.path.isdir(src_dir):
            checked_dirs.append([src_dir, pattern, target_dir])
        else:
            print("Can't find directory %s. Skipping" % src_dir, file=sys.stderr)
            continue
        last_compile_version = compiled_version
        pass

    if not checked_dirs:
        print("No directories found to check", file=sys.stderr)
        sys.exit(1)

    test_opts["compiled_version"] = last_compile_version

    for src_dir, pattern, target_dir in checked_dirs:
        target_dir = os.path.join(target_base, target_dir)
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir, ignore_errors=1)
        do_tests(src_dir, pattern, target_dir, test_opts)
