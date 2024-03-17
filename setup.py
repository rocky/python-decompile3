#!/usr/bin/env python
"""Setup script for the 'decompyle3' distribution."""

import sys

from setuptools import setup

SYS_VERSION = sys.version_info[0:2]
if SYS_VERSION < (3, 7):
    mess = f"\nThis package is not supported for Python version {sys.version[0:3]}."
    mess += "\nFor earlier versions, use uncompyle6."
    print(mess)
    raise Exception(mess)

setup(
    packages=[
        "decompyle3",
        "decompyle3.bin",
        "decompyle3.parsers",
        "decompyle3.scanners",
        "decompyle3.semantics",
    ]
)
