#  Copyright (c) 2016-2019 by Rocky Bernstein
"""
Python 3.6 bytecode decompiler scanner. Note:
although we don't support 3.6, 3.7 inherits from this.

This is here until we move everything over to that.
"""

from decompyle3.scanners.scanner3 import Scanner3

# bytecode verification, verify(), uses JUMP_OPS from here
from xdis.opcodes import opcode_36 as opc

class Scanner36(Scanner3):
    def __init__(self, show_asm=None, is_pypy=False):
        Scanner3.__init__(self, 3.6, show_asm, is_pypy)
        return

    def ingest(self, co, classname=None, code_objects={}, show_asm=None):
        tokens, customize = Scanner3.ingest(self, co, classname, code_objects, show_asm)
        not_pypy36 = not (self.version == 3.6 and self.is_pypy)
        for t in tokens:
            # The lowest bit of flags indicates whether the
            # var-keyword argument is placed at the top of the stack
            if not_pypy36 and t.op == self.opc.CALL_FUNCTION_EX and t.attr & 1:
                t.kind = "CALL_FUNCTION_EX_KW"
                pass
            elif t.op == self.opc.BUILD_STRING:
                t.kind = "BUILD_STRING_%s" % t.attr
            elif t.op == self.opc.CALL_FUNCTION_KW:
                t.kind = "CALL_FUNCTION_KW_%s" % t.attr
            elif t.op == self.opc.FORMAT_VALUE:
                if t.attr & 0x4:
                    t.kind = "FORMAT_VALUE_ATTR"
                    pass
            elif not_pypy36 and t.op == self.opc.BUILD_MAP_UNPACK_WITH_CALL:
                t.kind = "BUILD_MAP_UNPACK_WITH_CALL_%d" % t.attr
            elif not_pypy36 and t.op == self.opc.BUILD_TUPLE_UNPACK_WITH_CALL:
                t.kind = "BUILD_TUPLE_UNPACK_WITH_CALL_%d" % t.attr
            pass
        return tokens, customize
