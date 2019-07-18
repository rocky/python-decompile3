#  Copyright (c) 2018-2019 by Rocky Bernstein
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

"""Isolate Python 3 version-specific semantic actions here.
"""

from decompyle3.semantics.consts import TABLE_DIRECT

from xdis.code import iscode
from decompyle3.semantics.customize37 import customize_for_version37
from decompyle3.semantics.customize38 import customize_for_version38


def customize_for_version3(self, version):
    TABLE_DIRECT.update(
        {
            "comp_for": (" for %c in %c", (2, "store"), (0, "expr")),
            "conditionalnot": (
                "%c if not %c else %c",
                (2, "expr"),
                (0, "expr"),
                (4, "expr"),
            ),
            "except_cond2": ("%|except %c as %c:\n", (1, "expr"), (5, "store")),
            "function_def_annotate": ("\n\n%|def %c%c\n", -1, 0),
            # When a generator is a single parameter of a function,
            # it doesn't need the surrounding parenethesis.
            "call_generator": ("%c%P", 0, (1, -1, ", ", 100)),
            "importmultiple": ("%|import %c%c\n", 2, 3),
            "import_cont": (", %c", 2),
            "raise_stmt2": ("%|raise %c from %c\n", 0, 1),
            "store_locals": ("%|# inspect.currentframe().f_locals = __locals__\n",),
            "withstmt": ("%|with %c:\n%+%c%-", 0, 3),
            "withasstmt": ("%|with %c as (%c):\n%+%c%-", 0, 2, 3),
        }
    )

    assert version >= 3.7

    def n_classdef3(node):
        # class definition ('class X(A,B,C):')
        cclass = self.currentclass

        # Pick out various needed bits of information
        # * class_name - the name of the class
        # * subclass_info - the parameters to the class  e.g.
        #      class Foo(bar, baz)
        #               ----------
        # * subclass_code - the code for the subclass body
        subclass_info = None
        if node == "classdefdeco2":
            if self.version >= 3.6:
                class_name = node[1][1].attr
            elif self.version <= 3.3:
                class_name = node[2][0].attr
            else:
                class_name = node[1][2].attr
            build_class = node
        else:
            build_class = node[0]
            if self.version >= 3.6:
                if build_class == "build_class_kw":
                    mkfunc = build_class[1]
                    assert mkfunc == "mkfunc"
                    subclass_info = build_class
                    if hasattr(mkfunc[0], "attr") and iscode(mkfunc[0].attr):
                        subclass_code = mkfunc[0].attr
                    else:
                        assert mkfunc[0] == "load_closure"
                        subclass_code = mkfunc[1].attr
                        assert iscode(subclass_code)
                if build_class[1][0] == "load_closure":
                    code_node = build_class[1][1]
                else:
                    code_node = build_class[1][0]
                class_name = code_node.attr.co_name
            else:
                class_name = node[1][0].attr
                build_class = node[0]

        assert "mkfunc" == build_class[1]
        mkfunc = build_class[1]
        if mkfunc[0] in ("kwargs", "no_kwargs"):
            if 3.0 <= self.version <= 3.2:
                for n in mkfunc:
                    if hasattr(n, "attr") and iscode(n.attr):
                        subclass_code = n.attr
                        break
                    elif n == "expr":
                        subclass_code = n[0].attr
                    pass
                pass
            else:
                for n in mkfunc:
                    if hasattr(n, "attr") and iscode(n.attr):
                        subclass_code = n.attr
                        break
                    pass
                pass
            if node == "classdefdeco2":
                subclass_info = node
            else:
                subclass_info = node[0]
        elif build_class[1][0] == "load_closure":
            # Python 3 with closures not functions
            load_closure = build_class[1]
            if hasattr(load_closure[-3], "attr"):
                # Python 3.3 classes with closures work like this.
                # Note have to test before 3.2 case because
                # index -2 also has an attr.
                subclass_code = load_closure[-3].attr
            elif hasattr(load_closure[-2], "attr"):
                # Python 3.2 works like this
                subclass_code = load_closure[-2].attr
            else:
                raise "Internal Error n_classdef: cannot find class body"
            if hasattr(build_class[3], "__len__"):
                if not subclass_info:
                    subclass_info = build_class[3]
            elif hasattr(build_class[2], "__len__"):
                subclass_info = build_class[2]
            else:
                raise "Internal Error n_classdef: cannot superclass name"
        elif node == "classdefdeco2":
            subclass_info = node
            subclass_code = build_class[1][0].attr
        elif not subclass_info:
            if mkfunc[0] in ("no_kwargs", "kwargs"):
                subclass_code = mkfunc[1].attr
            else:
                subclass_code = mkfunc[0].attr
            if node == "classdefdeco2":
                subclass_info = node
            else:
                subclass_info = node[0]

        if node == "classdefdeco2":
            self.write("\n")
        else:
            self.write("\n\n")

        self.currentclass = str(class_name)
        self.write(self.indent, "class ", self.currentclass)

        self.print_super_classes3(subclass_info)
        self.println(":")

        # class body
        self.indent_more()
        self.build_class(subclass_code)
        self.indent_less()

        self.currentclass = cclass
        if len(self.param_stack) > 1:
            self.write("\n\n")
        else:
            self.write("\n\n\n")

        self.prune()

    self.n_classdef3 = n_classdef3

    TABLE_DIRECT.update(
        {
            "tryelsestmtl3": (
                "%|try:\n%+%c%-%c%|else:\n%+%c%-",
                (1, "suite_stmts_opt"),
                (3, "except_handler"),
                (5, "else_suitel"),
            ),
            "LOAD_CLASSDEREF": ("%{pattr}",),
        }
    )

    TABLE_DIRECT.update({"LOAD_CLASSDEREF": ("%{pattr}",)})

    if version >= 3.7:
        customize_for_version37(self, version)
        if version >= 3.8:
            customize_for_version38(self, version)
            pass  # version >= 3.8
        pass  # 3.7
    return
