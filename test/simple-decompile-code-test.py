#!/usr/bin/env python

from __future__ import print_function

from decompyle3.main import decompile
from xdis import sysinfo2float
import sys, inspect

def decompile_test():
    frame = inspect.currentframe()
    try:
        co = frame.f_code
        decompile(sysinfo2float(), co, sys.stdout, 1, 1)
        print()
    finally:
        del frame

decompile_test()
