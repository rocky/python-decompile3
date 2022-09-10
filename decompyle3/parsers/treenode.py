import sys
from decompyle3.scanners.tok import NoneToken, Token
from spark_parser.ast import AST as spark_AST

intern = sys.intern


class SyntaxTree(spark_AST):
    def __init__(self, *args, transformed_by=None, **kwargs):
        self.transformed_by = transformed_by
        super(SyntaxTree, self).__init__(*args, **kwargs)

    def isNone(self):
        """An SyntaxTree None token. We can't use regular list comparisons
        because SyntaxTree token offsets might be different"""
        return len(self.data) == 1 and NoneToken == self.data[0]

    def __repr__(self) -> str:
        return self.__repr1__("", None)

    def __repr1__(self, indent, sibNum=None) -> str:
        rv = str(self.kind)
        if sibNum is not None:
            rv = "%2d. %s" % (sibNum, rv)
        enumerate_children = False
        if len(self) > 1:
            rv += " (%d)" % (len(self))
            enumerate_children = True
        if self.transformed_by is not None:
            rv += f" (transformed by {self.transformed_by})"
            pass
        rv = indent + rv
        indent += "    "
        i = 0
        for node in self:
            if hasattr(node, "__repr1__"):
                if enumerate_children:
                    child = node.__repr1__(indent, i)
                else:
                    child = node.__repr1__(indent, None)
            else:
                inst = node.format(line_prefix="")
                if inst.startswith("\n"):
                    # Nuke leading \n
                    inst = inst[1:]
                if enumerate_children:
                    child = indent + "%2d. %s" % (i, inst)
                else:
                    child = indent + inst
                pass
            rv += "\n" + child
            i += 1
        return rv

    def first_child(self):
        for child in self:
            if isinstance(child, Token):
                return child
            if child is not None:
                child = child.first_child()
                if isinstance(child, Token):
                    return child
                pass
        return None

    def last_child(self):
        if len(self) > 0:
            child_index = -1
            child = self[-1]
            while isinstance(child, SyntaxTree) and len(child) == 0:
                # Skip over empty nonterminal reductions
                child_index -= 1
                child = self[child_index]
            if not isinstance(child, SyntaxTree):
                return child
            return child.last_child()
        return self
