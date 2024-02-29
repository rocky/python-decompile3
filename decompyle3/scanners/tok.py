#  Copyright (c) 2016-2020, 2023-2024 by Rocky Bernstein
#  Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
#  Copyright (c) 1999 John Aycock
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

import re
import sys
from typing import Optional, Union


def off2int(offset: int, prefer_last=True) -> int:
    if isinstance(offset, int):
        return offset
    else:
        assert isinstance(offset, str)
        offsets = list(map(int, offset.split("_")))
        if len(offsets) == 1:
            return offsets[0]
        else:
            assert 2 <= len(offsets) <= 3
            if len(offsets) == 3:
                offsets = offsets[:-1]
            assert len(offsets) == 2
            offset_1, offset_2 = offsets
        if offset_1 + 2 == offset_2:
            # This is an instruction with an extended arg.
            # For things that compare against offsets, we generally want the
            # later offset.
            return offset_2 if prefer_last else offset_1
        else:
            # Probably a "COME_FROM"-type offset, where the second number
            # is just a count, and not really an offset.
            return offset_1


class Token:
    """
    Class representing a byte-code instruction.

    A byte-code token is equivalent to Python 3's dis.instruction or
    the contents of one line as output by dis.dis().
    """

    # FIXME: match Python 3.4's terms:
    #    linestart = starts_line
    #    attr = argval
    #    pattr = argrepr
    def __init__(
        self,
        opname: str,
        attr=None,
        pattr=None,
        offset: Union[int, str] = -1,
        linestart=None,
        op=None,
        has_arg=None,
        opc=None,
        # extended arg indicates that this token was preceded
        # by EXTENDED_ARG. Note that the offset passed
        # is the EXTENDED_ARG's offset even though
        # the instruction associated with opname sits
        # at next offset
        has_extended_arg=False,
        tos_str=None,
        start_offset=None,
        optype: Optional[str] = None,
    ):
        self.attr = attr
        self.has_arg = has_arg
        self.kind = sys.intern(opname)
        self.linestart = linestart
        self.offset = f"{offset}_{offset+2}" if has_extended_arg else offset
        self.optype = optype
        self.pattr = pattr
        self.start_offset = start_offset
        self.tos_str = tos_str
        if has_arg is False:
            self.attr = None
            self.pattr = None

        if opc is None:
            try:
                from xdis.std import _std_api
            except KeyError as e:
                print(f"I don't know about Python version {e} yet.")
                try:
                    version_tuple = tuple(int(i) for i in str(e)[1:-1].split("."))
                except Exception:
                    pass
                else:
                    if version_tuple > (3, 9):
                        print("Python versions 3.9 and greater are not supported.")
                    else:
                        print(f"xdis might need to be informed about version {e}")
                return

            self.opc = _std_api.opc
        else:
            self.opc = opc
        if op is None:
            self.op = self.opc.opmap.get(self.kind, None)
        else:
            self.op = op

    def __eq__(self, o) -> bool:
        """'==' on kind and "pattr" attributes.
        It is okay if offsets and linestarts are different"""
        if isinstance(o, Token):
            return (self.kind == o.kind) and (
                (self.pattr == o.pattr) or self.attr == o.attr
            )
        else:
            # ?? do we need this?
            return self.kind == o

    def __ne__(self, o) -> bool:
        """'!=', but it's okay if offsets and linestarts are different"""
        return not self.__eq__(o)

    def __repr__(self) -> str:
        return str(self.kind)

    # def __str__(self):
    #     pattr = self.pattr if self.pattr is not None else ''
    #     prefix = '\n%3d   ' % self.linestart if self.linestart else (' ' * 6)
    #     return (prefix +
    #             ('%9s  %-18s %r' % (self.offset, self.kind, pattr)))

    def __str__(self) -> str:
        return self.format(line_prefix="")

    def format(self, line_prefix="", token_num=None) -> str:
        if token_num is not None:
            prefix = (
                "\n(%03d)%s L.%4d  " % (token_num, line_prefix, self.linestart)
                if self.linestart
                else ("(%03d)%s" % (token_num, " " * (9 + len(line_prefix))))
            )
        else:
            prefix = (
                "\n%s L.%4d  " % (line_prefix, self.linestart)
                if self.linestart
                else (" " * (9 + len(line_prefix)))
            )
        offset_opname = "%8s  %-17s" % (self.offset, self.kind)

        if not self.has_arg:
            return "%s%s" % (prefix, offset_opname)
        argstr = "%6d " % self.attr if isinstance(self.attr, int) else (" " * 7)
        name = self.kind

        if self.has_arg:
            pattr = self.tos_str if self.tos_str is not None else self.pattr
            if self.opc:
                if self.op in self.opc.JREL_OPS:
                    if not self.pattr.startswith("to "):
                        pattr = "to " + self.pattr
                elif self.op in self.opc.JABS_OPS:
                    self.pattr = str(self.pattr)
                    if not self.pattr.startswith("to "):
                        pattr = "to " + str(self.pattr)
                    pass
                elif self.op in self.opc.CONST_OPS:
                    if name == "LOAD_STR":
                        pattr = self.attr
                    elif name == "LOAD_CODE":
                        return "%s%s%s %s" % (prefix, offset_opname, argstr, pattr)
                    else:
                        return "%s%s        %r" % (prefix, offset_opname, pattr)

                elif self.op in self.opc.hascompare:
                    if isinstance(self.attr, int):
                        pattr = self.opc.cmp_op[self.attr]
                    return "%s%s%s %s" % (prefix, offset_opname, argstr, pattr)
                elif self.op in self.opc.hasvargs:
                    return "%s%s%s" % (prefix, offset_opname, argstr)
                elif name == "LOAD_ASSERT":
                    return "%s%s        %s" % (prefix, offset_opname, pattr)
                elif self.op in self.opc.NAME_OPS:
                    return "%s%s%s %s" % (prefix, offset_opname, argstr, pattr)
                elif name == "EXTENDED_ARG":
                    return "%s%s%s 0x%x << %s = %s" % (
                        prefix,
                        offset_opname,
                        argstr,
                        self.attr,
                        self.opc.EXTENDED_ARG_SHIFT,
                        pattr,
                    )
                # And so on. See xdis/bytecode.py get_instructions_bytes
                pass
        elif re.search(r"_\d+$", self.kind):
            return "%s%s%s" % (prefix, offset_opname, argstr)
        else:
            pattr = ""
        return "%s%s%s %r" % (prefix, offset_opname, argstr, pattr)

    def __hash__(self):
        return hash(self.kind)

    def __getitem__(self, i: int):
        raise IndexError

    def off2int(self, prefer_last=True) -> int:
        """
        Return an offset for this token. Note that the
        token type can sometimes be a string when the token
        encompasses one or more EXTENDED_ARG instructions.
        """
        return off2int(self.offset, prefer_last)


NoneToken = Token("LOAD_CONST", offset=-1, attr=None, pattr=None)
