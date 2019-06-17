from decompyle3.show import maybe_show_tree
from copy import copy
import sys

from xdis.code import iscode
from spark_parser import GenericASTTraversal, GenericASTTraversalPruningException
from decompyle3.scanner import Code
from decompyle3.parsers.treenode import SyntaxTree


class TreeTransform(GenericASTTraversal, object):
    def __init__(self, scanner, parser, build_ast, show_ast=None):
        self.showast = show_ast
        self.build_ast = build_ast
        self.currentclass = None
        self.scanner = scanner
        self.p = parser
        self.hide_internal = True
        self.ast_errors = []
        return

    def str_with_template(self, ast):
        sys.stdout.write(str(ast))

    def preorder(self, node=None):
        """Walk the tree in roughly 'preorder' (a bit of a lie explained below).
        For each node with typestring name *name* if the
        node has a method called n_*name*, call that before walking
        children. If there is no method define, call a
        self.default(node) instead. Subclasses of GenericASTTtraversal
        ill probably want to override this method.

        In typical use a node with children can call "preorder" in any
        order it wants which may skip children or order then in ways
        other than first to last.  In fact, this this happens.  So in
        this sense this function not strictly preorder.
        """
        if node is None:
            node = self.ast

        try:
            name = "n_" + self.typestring(node)
            if hasattr(self, name):
                func = getattr(self, name)
                node = func(node)
            else:
                node = self.default(node)
        except GenericASTTraversalPruningException:
            return

        for i, kid in enumerate(node):
            node[i] = self.preorder(kid)
        return node

    def default(self, node):
        # print(f"node is {node.kind}")
        return node

        # if key.kind in table:
        #     self.template_engine(table[key.kind], node)
        #     self.prune()

    def n_ifstmt(self, node):
        """Here we are just going to check if we can turn an 'ifstmt' into 'assert'"""
        testexpr = node[0]
        ifstmts_jump = node[1]
        if testexpr != "testexpr" or node[1] != "_ifstmts_jump":
            # No dice
            return node
        stmts = ifstmts_jump[0]
        if stmts in ("c_stmts",) and len(stmts) == 1:
            stmt = stmts[0]
            raise_stmt = stmt[0]
            if raise_stmt == "raise_stmt1" and len(testexpr[0]) == 2:
                assert_expr = testexpr[0][0]
                assert_expr.kind = "assert_expr"
                jmp_true = testexpr[0][1]
                expr = raise_stmt[0]
                RAISE_VARARGS_1 = raise_stmt[1]
                if expr[0] == "call":
                    # ifstmt
                    #     0. testexpr
                    #         testtrue (2)
                    #             0. expr
                    #     1. _ifstmts_jump (2)
                    #         0. c_stmts
                    #             stmt
                    #                 raise_stmt1 (2)
                    #                     0. expr
                    #                         call (3)
                    #                     1. RAISE_VARARGS_1
                    # becomes:
                    # assert2 ::= assert_expr jmp_true LOAD_ASSERT expr RAISE_VARARGS_1 COME_FROM
                    call = expr[0]
                    LOAD_ASSERT = call[0]
                    expr = call[1][0]
                    node = SyntaxTree(
                        "assert2", [assert_expr, jmp_true, LOAD_ASSERT, expr, RAISE_VARARGS_1]
                    )
                else:
                    # ifstmt
                    #   0. testexpr (2)
                    #      testtrue
                    #       0. expr
                    #   1. _ifstmts_jump (2)
                    #      0. c_stmts
                    #        stmts
                    #           raise_stmt1 (2)
                    #             0. expr
                    #                  LOAD_ASSERT
                    #             1.   RAISE_VARARGS_1
                    # becomes:
                    # assert ::= assert_expr jmp_true LOAD_ASSERT RAISE_VARARGS_1 COME_FROM
                    LOAD_ASSERT = expr[0]
                    node = SyntaxTree(
                        "assert", [assert_expr, jmp_true, LOAD_ASSERT, RAISE_VARARGS_1]
                    )
                pass
            pass
        return node

    def traverse(self, node, is_lambda=False):
        node = self.preorder(node)
        return node

    def transform(self, ast):
        self.ast = copy(ast)
        self.ast = self.traverse(self.ast, is_lambda=False)
        maybe_show_tree(self, self.ast)
        return self.ast

    # Write template_engine
    # def template_engine
