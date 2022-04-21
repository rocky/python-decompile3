#  Copyright (c) 2016-2019, 2021 by Rocky Bernstein
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
"""
Python 3.7 bytecode decompiler scanner

Does some additional massaging of xdis-disassembled instructions to
make things easier for decompilation.

This sets up opcodes Python's 3.7 and calls a generalized
scanner routine for Python 3.
"""

from decompyle3.scanners.scanner37base import Scanner37Base

from decompyle3.scanner import Token

# bytecode verification, verify(), uses JUMP_OPs from here
from xdis.opcodes import opcode_37 as opc

# bytecode verification, verify(), uses JUMP_OPS from here
JUMP_OPs = opc.JUMP_OPS


class Scanner37(Scanner37Base):
    def __init__(self, show_asm=None, debug=False, is_pypy=False):
        Scanner37Base.__init__(self, (3, 7), show_asm, is_pypy)
        self.debug = debug
        return

    pass

    def bound_collection(
        self, tokens: list, t: Token, i: int, collection_type: str, collection_enum: 0
    ):
        count = t.attr
        assert isinstance(count, int)

        n = len(tokens)
        assert count <= i
        collection_start = i - count

        # For small lists don't bother
        if count < 5:
            return tokens[: i + 1]

        for j in range(collection_start, count):
            if tokens[j].kind != "LOAD_CONST":
                return tokens
        # If we go there all instructions before tokens[i] are LOAD_CONST and we can replace
        # add a boundary marker and change LOAD_CONST to something else
        new_tokens = tokens[:collection_start]
        start_offset = tokens[collection_start].offset
        new_tokens.append(
            Token(
                opname="COLLECTION_START",
                attr=collection_enum,
                pattr=collection_type,
                offset=f"{start_offset}_0",
                has_arg=True,
                opc=self.opc,
                has_extended_arg=False,
            )
        )
        for j in range(collection_start, i):
            new_tokens.append(
                Token(
                    opname="ADD_CONST",
                    attr=tokens[j].attr,
                    pattr=tokens[j].pattr,
                    offset=tokens[j].offset,
                    has_arg=True,
                    linestart=tokens[j].linestart,
                    opc=self.opc,
                    has_extended_arg=False,
                )
            )
        new_tokens.append(
            Token(
                opname=f"BUILD_{collection_type}",
                attr=t.attr,
                pattr=t.pattr,
                offset=t.offset,
                has_arg=t.has_arg,
                linestart=t.linestart,
                opc=t.opc,
                has_extended_arg=False,
            )
        )
        return new_tokens

    def ingest(self, co, classname=None, code_objects={}, show_asm=None) -> tuple:
        tokens, customize = Scanner37Base.ingest(
            self, co, classname, code_objects, show_asm
        )
        new_tokens = []
        for i, t in enumerate(tokens):
            # things that smash new_tokens like BUILD_LIST have to come first.
            if t.op in (self.opc.BUILD_LIST, self.opc.BUILD_SET):
                collection_type = t.kind.split("_")[1]
                new_tokens = self.bound_collection(
                    tokens, t, i, f"CONST{collection_type}", 0
                )
                continue
            # The lowest bit of flags indicates whether the
            # var-keyword argument is placed at the top of the stack
            elif t.op == self.opc.CALL_FUNCTION_EX and t.attr & 1:
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
            elif t.op == self.opc.BUILD_MAP_UNPACK_WITH_CALL:
                t.kind = "BUILD_MAP_UNPACK_WITH_CALL_%d" % t.attr
            elif (not self.is_pypy) and t.op == self.opc.BUILD_TUPLE_UNPACK_WITH_CALL:
                t.kind = "BUILD_TUPLE_UNPACK_WITH_CALL_%d" % t.attr
            new_tokens.append(t)

        return new_tokens, customize


if __name__ == "__main__":
    from xdis.version_info import PYTHON_VERSION_TRIPLE, version_tuple_to_str

    if PYTHON_VERSION_TRIPLE[:2] == (3, 7):
        import inspect

        co = inspect.currentframe().f_code  # type: ignore
        tokens, customize = Scanner37().ingest(co)
        for t in tokens:
            print(t.format())
        pass
    else:
        print(f"Need to be Python 3.7 to demo; I am version {version_tuple_to_str}.")
