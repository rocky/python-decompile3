#  Copyright (c) 2019, 2021-2022 by Rocky Bernstein
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
"""Python 3.9 bytecode decompiler scanner.

Does some token massaging of xdis-disassembled instructions to make
things easier for decompilation.

This sets up opcodes Python's 3.9 and calls a generalized
scanner routine for Python 3.7 and up.
"""

# bytecode verification, verify(), uses JUMP_OPs from here
from xdis.opcodes import opcode_38 as opc

from decompyle3.scanners.scanner38 import Scanner38

# bytecode verification, verify(), uses JUMP_OPS from here
JUMP_OPs = opc.JUMP_OPS


class Scanner39(Scanner38):
    def __init__(self, show_asm=None):
        Scanner38.__init__(self, (3, 9), show_asm)
        return

    pass


if __name__ == "__main__":
    from xdis.version_info import PYTHON_VERSION

    if PYTHON_VERSION == 3.9:
        import inspect

        co = inspect.currentframe().f_code  # type: ignore
        tokens, customize = Scanner39().ingest(co)
        for t in tokens:
            print(t.format())
        pass
    else:
        print(f"Need to be Python 3.9 to demo; I am {PYTHON_VERSION}.")
