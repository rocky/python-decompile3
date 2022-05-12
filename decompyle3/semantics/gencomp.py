#  Copyright (c) 2022 by Rocky Bernstein
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
Generators and comprehension functions
"""


from spark_parser.ast import GenericASTTraversalPruningException
from typing import Optional
from xdis import iscode

from decompyle3.parsers.main import get_python_parser
from decompyle3.scanner import Code
from decompyle3.semantics.consts import PRECEDENCE
from decompyle3.semantics.helper import is_lambda_mode
from decompyle3.scanners.tok import Token


class ComprehensionMixin:
    """
    These functions hand nonterminal common actions that occur
    when encountering a generator or some sort of comprehension.

    What is common about these is that often the nonterminal has
    a code object whose decompilation needs to be melded into the resulting
    Python source code. In source code, the implicit function calls
    are not seen.
    """

    def closure_walk(self, node, collection_index: int):
        """Dictionary and Set comprehensions using closures."""
        p = self.prec

        code_index = 0 if node[0] == "load_genexpr" else 1
        tree = self.get_comprehension_function(node, code_index=code_index)

        if tree.kind in ("stmts", "lambda_start"):
            tree = tree[0]

        # Remove single reductions as in ("stmts", "sstmt"):
        while len(tree) == 1 or tree.kind in ("return_expr_lambda",):
            tree = tree[0]

        if tree == "genexpr_func_async":
            store = tree[2]
            iter_index = 3
            collection_index = 3
        elif tree in ("genexpr_func", "dict_comp_func", "set_comp_func"):
            store = tree[3]
            iter_index = 4
        elif tree == "set_comp":
            tree = tree[1][0]
            assert tree == "set_for", tree.kind
            store = tree[2]
            iter_index = 3
            collection_index = 4
        else:
            store = tree[4]
            iter_index = 5

        if node[collection_index] == "get_iter":
            expr = node[collection_index][0]
            assert expr == "expr", expr.kind
            collection = expr
        else:
            collection = node[collection_index]
        n = tree[iter_index]
        list_if = None
        write_if = False

        assert n in ("comp_iter", "set_iter")

        # Find inner-most node.
        while n == "comp_iter":
            n = n[0]  # recurse one step

            if n in ("list_for", "comp_for"):
                store = n[2]
                n = n[3]
            elif n[0].kind == "c_compare":
                list_if = n
                n = n[-1]
            elif n in (
                "comp_if",
                "comp_if_not",
                "list_if",
                "list_if_and_or",
                "list_if_not",
                "list_if_or_not",
            ):
                # FIXME: most of the grammar start with expr_...
                # Some of the older ones can be: expr <jump> <iter>
                # This may disappear though.
                if n[0].kind == "expr":
                    list_if = n
                    n = n[-1]
                elif n[0].kind in ("expr_pjif", "expr_pjiff"):
                    list_if = n
                    n = n[1]
                    assert n == "comp_iter"
                elif n[0].kind in ("or_jump_if_false_cf", "or_jump_if_false_loop_cf"):
                    list_if = n[1]
                    n = n[1]
                else:
                    if len(n) == 2:
                        list_if = n[0]
                        n = n[1]
                    else:
                        list_if = n[1]
                        n = n[2]
                pass
            pass

        assert n in ("comp_body", "set_iter"), n.kind

        self.preorder(n[0])
        if node == "generator_exp_async":
            self.write(" async")
        self.write(" for ")
        self.preorder(store)
        self.write(" in ")
        self.preorder(collection)
        if list_if:
            if write_if:
                self.write(" if ")
            self.preorder(list_if)
        self.prec = p

    def comprehension_walk(
        self, node, iter_index: Optional[int], code_index: int = -5,
    ):
        p = self.prec
        self.prec = PRECEDENCE["lambda_body"] - 1

        # FIXME: clean this up
        if node == "dict_comp":
            cn = node[1]
        elif node in ("generator_exp", "generator_exp_async"):
            if node[0] == "load_genexpr":
                load_genexpr = node[0]
            elif node[1] == "load_genexpr":
                load_genexpr = node[1]
            cn = load_genexpr[0]
        else:
            if len(node[1]) > 1 and hasattr(node[1][1], "attr"):
                # Python 3.3+ does this
                cn = node[1][1]
            else:
                assert False, "Can't find code for comprehension"

        assert iscode(cn.attr)

        code = Code(cn.attr, self.scanner, self.currentclass, self.debug_opts["asm"])

        # FIXME: is there a way we can avoid this?
        # The problem is that in filter in top-level list comprehensions we can
        # encounter comprehensions of other kinds, and lambdas
        if is_lambda_mode(self.compile_mode):
            p_save = self.p
            self.p = get_python_parser(
                self.version, compile_mode="exec", is_pypy=self.is_pypy,
            )
            tree = self.build_ast(code._tokens, code._customize, code)
            self.p = p_save
        else:
            tree = self.build_ast(code._tokens, code._customize, code)
        self.customize(code._customize)

        # Remove single reductions as in ("stmts", "sstmt"):
        while len(tree) == 1:
            tree = tree[0]

        if tree == "stmts":
            # FIXME: rest is a return None?
            # Verify this
            # rest = tree[1:]
            tree = tree[0]
        elif tree == "lambda_start":
            assert len(tree) <= 3
            tree = tree[-2]
            if tree == "return_expr_lambda":
                tree = tree[1]
            pass

        if tree in ("genexpr_func_async",):
            if tree[3] == "comp_iter":
                iter_index = 3

        n = tree[iter_index]
        assert n == "comp_iter", n
        list_if = None
        write_if = False

        # Find the comprehension body. It is the inner-most
        # node that is not list_.. .
        while n == "comp_iter":  # list_iter
            n = n[0]  # recurse one step
            if n == "comp_for":
                if n[0] == "SETUP_LOOP":
                    n = n[4]
                else:
                    n = n[3]
            elif n == "comp_if":
                n = n[1]
            elif n in (
                "comp_if_not",
                "comp_if_not_and",
                "comp_if_not_or",
                "comp_if_or",
            ):
                list_if = n
                write_if = True
                n = n[-1]
                assert n == "comp_iter"

        assert n == "comp_body", n.kind

        self.preorder(n[0])
        if node == "generator_exp_async":
            self.write(" async")
            iter_var_index = 2
        else:
            iter_var_index = iter_index - 1
        self.write(" for ")
        self.preorder(tree[iter_var_index])
        self.write(" in ")
        if node[2] == "expr":
            iter_expr = node[2]
        elif node[3] == "get_aiter":
            iter_expr = node[3]
        else:
            iter_expr = node[-3]
        assert iter_expr in ("expr", "get_aiter"), iter_expr
        self.preorder(iter_expr)
        self.preorder(tree[iter_index])
        if list_if:
            if write_if:
                self.write(" if ")
            self.preorder(list_if)
        self.prec = p

    def comprehension_walk_newer(
        self,
        node,
        iter_index: Optional[int],
        code_index: int = -5,
        collection_node=None,
    ):
        """Non-closure-based comprehensions.

        Note: there are also other comprehensions.
        """
        # FIXME: DRY with listcomp_closure3

        p = self.prec
        self.prec = PRECEDENCE["lambda_body"] - 1

        # FIXME? Nonterminals in grammar maybe should be split out better?
        # Maybe test on self.compile_mode?
        if (
            isinstance(node[0], Token)
            and node[0].kind.startswith("LOAD")
            and iscode(node[0].attr)
        ):
            if node[3] == "get_aiter":
                compile_mode = self.compile_mode
                self.compile_mode = "genexpr"
                is_lambda = self.is_lambda
                self.is_lambda = True
                try:
                    tree = self.get_comprehension_function(node, code_index)
                except GenericASTTraversalPruningException:
                    pass
                self.compile_mode = compile_mode
                self.is_lambda = is_lambda
            else:
                tree = self.get_comprehension_function(node, code_index)
        elif (
            len(node) > 2
            and isinstance(node[2], Token)
            and node[2].kind.startswith("LOAD")
            and iscode(node[2].attr)
        ):
            tree = self.get_comprehension_function(node, 2)
        else:
            tree = node

        # Pick out important parts of the comprehension:
        # * the variable we iterate over: "store"
        # * the results we accumulate: "n"

        store = None
        if node == "list_comp_async":
            # We have two different kinds of grammar rules:
            #   list_comp_async ::= LOAD_LISTCOMP LOAD_STR MAKE_FUNCTION_0 expr ...
            # and:
            #  list_comp_async  ::= BUILD_LIST_0 LOAD_ARG list_afor2
            if tree[0] == "expr" and tree[0][0] == "list_comp_async":
                tree = tree[0][0]
            if tree[0] == "BUILD_LIST_0":
                list_afor2 = tree[2]
                assert list_afor2 == "list_afor2"
                store = list_afor2[1]
                assert store == "store"
                n = list_afor2[3] if list_afor2[3] == "list_iter" else list_afor2[2]
            else:
                # ???
                pass
        elif node.kind in ("dict_comp_async", "set_comp_async"):
            # We have two different kinds of grammar rules:
            #   dict_comp_async ::= LOAD_DICTCOMP LOAD_STR MAKE_FUNCTION_0 expr ...
            #   set_comp_async  ::= LOAD_SETCOMP LOAD_STR MAKE_FUNCTION_0 expr ...
            # and:
            #  dict_comp_async  ::= BUILD_MAP_0 genexpr_func_async
            #  set_comp_async   ::= BUILD_SET_0 genexpr_func_async
            if tree[0] == "expr":
                tree = tree[0]

            if tree[0].kind in ("BUILD_MAP_0", "BUILD_SET_0"):
                genexpr_func_async = tree[1]
                if genexpr_func_async == "genexpr_func_async":
                    store = genexpr_func_async[2]
                    assert store.kind.startswith("store")
                    n = genexpr_func_async[3]
                else:
                    set_afor2 = genexpr_func_async
                    assert set_afor2 == "set_afor2"
                    n = set_afor2[1]
                    store = n[1]
                    collection_node = node[3]
            else:
                # ???
                pass

        elif node == "list_afor":
            collection_node = node[0]
            list_afor2 = node[1]
            assert list_afor2 == "list_afor2"
            store = list_afor2[1]
            assert store == "store"
            n = list_afor2[2]
        elif node == "set_afor2":
            collection_node = node[0]
            set_iter_async = node[1]
            assert set_iter_async == "set_iter_async"

            store = set_iter_async[1]
            assert store == "store"
            n = set_iter_async[2]
        else:
            n = tree[iter_index]

        if tree in (
            "dict_comp_func",
            "genexpr_func_async",
            "generator_exp",
            "list_comp",
            "set_comp",
            "set_comp_func",
            "set_comp_func_header",
        ):
            for k in tree:
                if k.kind in ("comp_iter", "list_iter", "set_iter", "await_expr"):
                    n = k
                elif k == "store":
                    store = k
                    pass
                pass
            pass
        elif tree.kind in ("list_comp_async", "dict_comp_async", "set_afor2"):
            # Handled this condition above.
            pass
        else:
            # FIXME: we get this when we parse lambda's explicitly.
            # And here we've already printed/handled the list comprehension
            # this iteration is duplicate in seeing the list-comprehension code
            # item again. Is this a larger duplicate parsing problem?
            # Not sure what the best this thing to do is.
            # try:
            #     n
            # except:
            #     from trepan.api import debug; debug()

            if n.kind in ("RETURN_VALUE_LAMBDA", "return_expr_lambda"):
                self.prune()

            assert n.kind in ("list_iter", "comp_iter", "set_iter_async"), n

        # FIXME: I'm not totally sure this is right.

        # Find the list comprehension body. It is the inner-most
        # node that is not list_.. .
        if_nodes = []
        if_node_parent = None
        comp_for = None
        comp_store = None
        if n == "comp_iter":
            comp_for = n
            if not store:
                comp_store = tree[3]

        # Iterate to find the inner-most "store".
        # We'll come back to the list iteration below.
        while n in (
            "list_iter",
            "list_afor",
            "list_afor2",
            "comp_iter",
            "set_afor",
            "set_afor2",
            "set_iter",
            "set_iter_async",
        ):
            # iterate one nesting deeper
            if n in ("list_afor", "set_afor"):
                n = n[1]
            elif n in ("list_afor2", "set_afor2", "set_iter_async"):
                if n[1] == "store":
                    store = n[1]
                n = n[3] if n[3] in ("list_iter", "set_iter") else n[2]
            else:
                n = n[0]

            if n in ("comp_for", "list_for", "set_for"):
                collection_node = n
                if n[2] == "store" and not store:
                    store = n[2]
                    if not comp_store:
                        comp_store = store
                n = n[3]
                assert n.kind in ("comp_iter", "list_iter", "set_iter")
            elif n in ("list_if_chained",):
                #  list_if_chained ::= list_if_compare ... list_iter
                if_nodes.append(n[0])
                assert n[0] == "list_if_compare"
                n = n[-1]
                assert n == "list_iter"
            elif n in (
                "comp_if_not_and",
                "comp_if_or",
                "comp_if_or2",
                "comp_if_or_not",
                "comp_if_not_or",
            ):
                if_nodes.append(n)
                n = n[-1]
                assert n == "comp_iter"
            elif n in (
                "list_if",
                "list_if_not",
                "list_if37",
                "list_if37_not",
                "comp_if",
                "comp_if_not",
            ):
                if n in ("list_if37", "list_if37_not", "comp_if"):
                    if n == "comp_if":
                        if_nodes.append(n[0])
                    n = n[1]
                else:
                    if n in ("comp_if_not",):
                        if_nodes.append(n)
                    else:
                        if_node_parent = n
                        if_nodes.append(n[0])
                    if n[1] == "store":
                        store = n[1]
                    n = n[-2] if n[-1] == "come_from_opt" else n[-1]
                    pass
            elif n.kind == "list_if_and_or":
                if_nodes.append(n[-1][0])
                n = n[-1]
                assert n == "list_iter"
            pass

        # Python 2.7+ starts including set_comp_body
        # Python 3.5+ starts including set_comp_func
        assert store, "Couldn't find store in list/set comprehension"

        # A problem created with later Python code generation is that there
        # is a lambda set up with a dummy argument name that is then called
        # So we can't just translate that as is but need to replace the
        # dummy name. Below we are picking out the variable name as seen
        # in the code. And trying to generate code for the other parts
        # that don't have the dummy argument name in it.
        # Another approach might be to be able to pass in the source name
        # for the dummy argument.

        if node not in ("list_afor", "set_afor"):
            # FIXME decompile_cfg doesn't have to do this. Find out why.
            self.preorder(n if n == "await_expr" else n[0])

        if node.kind in (
            "dict_comp_async",
            "genexpr_func_async",
            "list_afor",
            "list_comp_async",
            "set_afor2",
            "set_comp_async",
        ):
            self.write(" async")
            in_node_index = None
            for i, child in enumerate(node):
                if child.kind in ("expr", "expr_get_aiter", "get_aiter", "get_iter"):
                    in_node_index = i
                    break
            assert in_node_index is not None
        elif len(node) >= 3 and node[3] == "expr":
            in_node_index = 3
            collection_node = node[3]
            assert collection_node == "expr"
        elif node == "comp_body":
            collection_node = node
        else:
            in_node_index = -3

        self.write(" for ")

        if comp_store:
            self.preorder(comp_store)
        else:
            self.preorder(store)

        self.write(" in ")

        if node == "list_afor":
            list_afor2 = node[1]
            assert list_afor2 == "list_afor2"
            list_iter = list_afor2[2]
            assert list_iter == "list_iter"
            self.preorder(collection_node)
            if_nodes = []
        elif node == "set_comp_async":
            self.preorder(collection_node)
            if_nodes = []
        elif node == "list_comp_async":
            self.preorder(node[in_node_index])
        elif is_lambda_mode(self.compile_mode):
            if node == "list_comp_async":
                from trepan.api import debug

                debug()
                self.preorder(node[1])
            elif collection_node is None:
                assert node[3] in ("get_aiter", "get_iter"), node[3].kind
                self.preorder(node[3])
            else:
                self.preorder(collection_node)
        else:
            if not collection_node:
                collection_node = node[in_node_index]
            self.preorder(collection_node)

        # Here is where we handle nested list iterations which
        # includes their corresponding "if" conditions.
        if tree in ("list_comp", "set_comp"):
            list_iter = tree[1]
            assert list_iter in ("list_iter", "set_iter")
            list_for = list_iter[0]
            if list_for in ("list_for", "set_for"):
                # In the grammar we have:
                #    list_for ::= _  for_iter store list_iter ...
                # or
                #    set_for ::= _   set_iter store set_iter ...
                list_iter_inner = list_for[3]
                assert list_iter_inner in ("list_iter", "set_iter")
                # If we have set_comp_body, we've done this above.
                if not (
                    list_iter_inner == "set_iter"
                    and list_iter_inner[0] == "set_comp_body"
                ):
                    self.preorder(list_iter_inner)
                    if if_node_parent == list_iter_inner[0]:
                        self.prec = p
                        return
                comp_store = None
                if_nodes = []
            pass

        if tree == "set_comp_func":
            # Handle nested comp_for iterations.
            comp_iter = tree[4]
            assert comp_iter in ("comp_iter", "await_expr")
            while comp_iter == "comp_iter":
                comp_for = comp_iter[0]
                if comp_for != "comp_for":
                    break
                self.preorder(comp_iter)
                if len(comp_for) < 4:
                    break
                comp_iter = comp_for[3]
            assert comp_store is None

        if comp_store:
            self.preorder(comp_store)
        for if_node in if_nodes:
            if if_node != "comp_if_or":
                self.write(" if ")
            if if_node in (
                "comp_if_not_and",
                "comp_if_not_or",
                "comp_if_or",
                "comp_if_or2",
                "comp_if_or_not",
            ):
                self.preorder(if_node)
            else:
                # FIXME: go over these to add more of this in the template,
                # not here.
                if if_node in ("list_if_not", "comp_if_not", "list_if37_not"):
                    self.write("not ")
                    pass
                self.prec = PRECEDENCE["lambda_body"] - 1
                self.preorder(if_node[0])
            pass
        self.prec = p

    def get_comprehension_function(self, node, code_index: int):
        """
        Build the body of a comprehension function and then
        find the comprehension node buried in the tree which may
        be surrounded with start-like symbols or dominiators,.
        """
        self.prec = PRECEDENCE["lambda_body"] - 1
        code_node = node[code_index]
        if code_node == "load_genexpr":
            code_node = code_node[0]

        code_obj = code_node.attr
        assert iscode(code_obj), code_node

        code = Code(code_obj, self.scanner, self.currentclass, self.debug_opts["asm"])

        # FIXME: is there a way we can avoid this?
        # The problem is that in filter in top-level list comprehensions we can
        # encounter comprehensions of other kinds, and lambdas
        if is_lambda_mode(self.compile_mode):
            p_save = self.p
            self.p = get_python_parser(
                self.version, compile_mode="exec", is_pypy=self.is_pypy,
            )
            tree = self.build_ast(
                code._tokens, code._customize, code, is_lambda=self.is_lambda
            )
            self.p = p_save
        else:
            tree = self.build_ast(
                code._tokens, code._customize, code, is_lambda=self.is_lambda
            )

        self.customize(code._customize)

        # skip over: sstmt, stmt, return, return_expr
        # and other singleton derivations
        if tree == "lambda_start":
            tree = tree[0]

        while len(tree) == 1 or (tree in ("stmt", "sstmt", "return", "return_expr")):
            self.prec = 100
            tree = tree[0]
        return tree
