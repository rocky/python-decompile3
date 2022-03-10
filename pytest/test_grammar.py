import re
from xdis import PYTHON_VERSION_TRIPLE, IS_PYPY
from decompyle3.parsers.main import get_python_parser, python_parser


def test_grammar():
    def check_tokens(tokens, opcode_set):
        remain_tokens = set(tokens) - opcode_set
        remain_tokens = set([re.sub(r"_\d+$", "", t) for t in remain_tokens])
        remain_tokens = set([re.sub("_CONT$", "", t) for t in remain_tokens])
        remain_tokens = set([re.sub("LOAD_CODE$", "", t) for t in remain_tokens])
        remain_tokens = set(remain_tokens) - opcode_set
        assert remain_tokens == set([]), "Remaining tokens %s\n====\n%s" % (
            remain_tokens,
            p.dump_grammar(),
        )

    p = get_python_parser(PYTHON_VERSION_TRIPLE, is_pypy=IS_PYPY)
    (lhs, rhs, tokens, right_recursive, dup_rhs) = p.check_sets()

    expect_lhs = set([])

    # We have custom rules that create the below.
    # await_expr can be remove after we create a p37/full_custom.py
    unused_rhs = set(["mkfunc"])

    expect_right_recursive = set([("designList", ("store", "DUP_TOP", "designList"))])

    expect_lhs.add("load_genexpr")
    expect_lhs.add("kv3")
    expect_lhs.add("lambda_start")  # Start symbol for lambda expressions

    unused_rhs = unused_rhs.union(
        set(
            """
    except_pop_except
    """.split()
        )
    )
    unused_rhs.add("classdefdeco1")
    unused_rhs.add("tryelsestmtc")

    assert expect_lhs == set(lhs)
    assert unused_rhs == set(rhs)
    assert expect_right_recursive == right_recursive

    expect_dup_rhs = frozenset(
        [
            ("COME_FROM",),
            ("CONTINUE",),
            ("JUMP_ABSOLUTE",),
            ("LOAD_CONST",),
            ("JUMP_LOOP",),
            ("JUMP_FORWARD",),
        ]
    )
    reduced_dup_rhs = dict((k, dup_rhs[k]) for k in dup_rhs if k not in expect_dup_rhs)
    if reduced_dup_rhs:
        print(
            "\nPossible duplicate RHS that might be folded, into one of the LHS symbols"
        )
        for k in reduced_dup_rhs:
            print(k, reduced_dup_rhs[k])
    # assert not reduced_dup_rhs, reduced_dup_rhs

    # ignore_set = set(
    #     """
    #         JUMP_LOOP CONTINUE
    #         COME_FROM COME_FROM_EXCEPT
    #         COME_FROM_EXCEPT_CLAUSE
    #         COME_FROM_LOOP COME_FROM_WITH
    #         COME_FROM_FINALLY ELSE
    #         LOAD_GENEXPR LOAD_ASSERT LOAD_SETCOMP LOAD_DICTCOMP LOAD_STR LOAD_CODE
    #         LAMBDA_MARKER
    #         RETURN_END_IF RETURN_END_IF_LAMBDA RETURN_VALUE_LAMBDA RETURN_LAST
    #         """.split()
    # )


def test_dup_rule():
    import inspect

    python_parser(
        inspect.currentframe().f_code,
        PYTHON_VERSION_TRIPLE,
        is_pypy=IS_PYPY,
        parser_debug={
            "dups": True,
            "transition": False,
            "reduce": False,
            "rules": False,
            "errorstack": None,
            "context": True,
        },
    )


if __name__ == "__main__":
    test_grammar()
    test_dup_rule()
