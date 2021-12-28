#!/usr/bin/env python
# Mode: -*- python -*-
#
# Copyright (c) 2015-2016, 2018, 2020-2021 by Rocky Bernstein <rb@dustyfeet.com>
#
import sys, os, getopt

from decompyle3.lambda_fns import decompile_lambda_fns
from decompyle3.version import __version__

program, ext = os.path.splitext(os.path.basename(__file__))

__doc__ = """
Usage:
  {0} [OPTIONS]... FILE
  {0} [--help | -h | -V | --version]

decompile all lambda functions FILE.
""".format(
    program
)

PATTERNS = ("*.pyc", "*.pyo")


def main():
    Usage_short = (
        """usage: %s FILE...
Type -h for for full help."""
        % program
    )

    if len(sys.argv) == 1:
        print("No file(s) given", file=sys.stderr)
        print(Usage_short, file=sys.stderr)
        sys.exit(1)

    try:
        opts, files = getopt.getopt(
            sys.argv[1:], "hVU", ["help", "version", "decompile_ng"]
        )
    except getopt.GetoptError as e:
        print("%s: %s" % (os.path.basename(sys.argv[0]), e), file=sys.stderr)
        sys.exit(-1)

    for opt, _ in opts:
        if opt in ("-h", "--help"):
            print(__doc__)
            sys.exit(1)
        elif opt in ("-V", "--version"):
            print("%s %s" % (program, __version__))
            sys.exit(0)
        else:
            print(opt)
            print(Usage_short, file=sys.stderr)
            sys.exit(1)

    success = 0
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
                            decompile_lambda_fns(filepath, sys.stdout)
                            print()
                            success += 1
                            total += 1
            elif os.path.exists(filename) and not os.path.islink(filename):
                if (
                    filename.endswith(".pyc")
                    or filename.endswith(".py")
                    or filename.endswith(".pyo")
                    or os.path.isdir(filename)
                ):
                    decompile_lambda_fns(
                        filename, sys.stdout, showasm=None, showast=False
                    )
                    print()
                    success += 1
                    total += 1
            else:
                print(f"Can't read {filename}; skipping", file=sys.stderr)
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
    print(f"total: {total}, success: {success}")
    return


if __name__ == "__main__":
    main()
