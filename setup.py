#!/usr/bin/env python
"""Setup script for the 'decompyle3' distribution."""

import sys

from __pkginfo__ import (
    author,
    author_email,
    install_requires,
    license,
    long_description,
    classifiers,
    entry_points,
    modname,
    py_modules,
    short_desc,
    __version__,
    web,
    zip_safe,
)

import setuptools

SYS_VERSION = sys.version_info[0:2]
if SYS_VERSION < (3, 7):
    mess = f"\nThis package is not supported for Python version {sys.version[0:3]}."
    mess += "\nFor earlier versions, use uncompyle6."
    print(mess)
    raise Exception(mess)

setuptools.setup(
    author=author,
    author_email=author_email,
    classifiers=classifiers,
    description=short_desc,
    entry_points=entry_points,
    install_requires=install_requires,
    license=license,
    long_description=long_description,
    name=modname,
    packages=setuptools.find_packages(),
    py_modules=py_modules,
    test_suite="nose.collector",
    url=web,
    tests_require=["nose>=1.0"],
    version=__version__,
    zip_safe=zip_safe,
)
