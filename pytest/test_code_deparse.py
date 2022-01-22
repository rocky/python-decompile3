import pytest
from xdis.version_info import PYTHON_VERSION_TRIPLE
from decompyle3 import code_deparse
from decompyle3.semantics.pysource import DEFAULT_DEBUG_OPTS

from io import StringIO

out = StringIO()


def run_deparse(expr: str, compile_mode: bool, debug=False) -> object:
    debug_opts = dict(DEFAULT_DEBUG_OPTS)
    if debug:
        debug_opts["reduce"] = True
        debug_opts["asm"] = "both"

    orig_compile_mode = compile_mode
    if compile_mode == "lambda":
        compile_mode = "eval"
    code = compile(expr + "\n", "<string %s>" % expr, compile_mode)
    if debug:
        import dis

        print(dis.dis(code))
    deparsed = code_deparse(
        code, out=out, compile_mode=orig_compile_mode, debug_opts=DEFAULT_DEBUG_OPTS
    )
    return deparsed


# FIXME: DRY this code
@pytest.mark.skipif(
    not (3, 7) <= PYTHON_VERSION_TRIPLE < (3, 9), reason="asssume Python 3.7 or 3.8"
)
def test_single_mode() -> None:
    expressions = (
        "1",
        "i and (j or k)",
        "i and j or k",
        "i or (j and k)",
        "j % 4",
        "i = 1",
        "i += 1",
        "i = j % 4",
        "i = {}",
        "i = []",
        # "for i in range(10):\n    i\n",
        # "for i in range(10):\n    for j in range(10):\n        i + j\n",
        "(i for i in f if 0 < i < 4)",
        # "[i for pair in p if pair for i in f]",
        # Inconsequential differences in spaces.
        # "try:\n    i\nexcept Exception:\n    j\nelse:\n    k",
    )

    for expr in expressions:
        # print("XXX", expr)
        try:
            deparsed = run_deparse(expr, compile_mode="single", debug=False)
        except:
            assert False, expr
            continue

        if deparsed.text != (expr + "\n"):
            from decompyle3.show import maybe_show_tree

            deparsed.showast = {"Full": True}
            maybe_show_tree(deparsed, deparsed.ast)
        assert deparsed.text == expr + "\n" if deparsed.text.endswith("\n") else expr


@pytest.mark.skipif(
    not (3, 7) <= PYTHON_VERSION_TRIPLE < (3, 9), reason="asssume Python 3.7 or 3.8"
)
def test_eval_mode():
    expressions = (
        "1",
        "j % 4",
        "k == 1 or k == 2",
        "i and (j or k)",
        "i and j or k",
    )

    for expr in expressions:
        try:
            deparsed = run_deparse(expr, compile_mode="eval", debug=False)
        except:
            assert False, expr
            continue

        if deparsed.text != expr:
            from decompyle3.show import maybe_show_tree

            deparsed.showast = {"Full": True}
            maybe_show_tree(deparsed, deparsed.ast)
        assert deparsed.text == expr


@pytest.mark.skipif(
    not (3, 7) <= PYTHON_VERSION_TRIPLE < (3, 9), reason="asssume Python 3.7 or 3.8"
)
def test_lambda_mode():
    expressions = (
        "lambda d=b'': 5",
        "lambda *, d=0: d",
        "lambda x: 1 if x < 2 else 3",
        "lambda y: x * y",
        "lambda n: True if n >= 95 and n & 1 else False",
        "lambda: (yield from f())",
    )

    for expr in expressions:
        try:
            deparsed = run_deparse(expr, compile_mode="lambda", debug=False)
        except:
            assert False, expr
            continue
        if deparsed.text != expr:
            from decompyle3.show import maybe_show_tree

            deparsed.showast = {"Full": True}
            maybe_show_tree(deparsed, deparsed.ast)
        assert deparsed.text == expr + "\n" if deparsed.text.endswith("\n") else expr


if __name__ == "__main__":
    # test_eval_mode()
    test_lambda_mode()
    # test_single_mode()
