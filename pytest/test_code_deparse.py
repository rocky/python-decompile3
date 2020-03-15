from decompyle3 import code_deparse

from io import StringIO

out = StringIO()

def run_deparse(expr: str, compile_mode: bool, debug=False) -> object:
    if debug:
        debug_opts = {"asm": "both", "tree": True, "grammar": True}
    else:
        debug_opts = {"asm": False, "tree": False, "grammar": False}

    if compile_mode == "lambda":
        compile_mode = "eval"
    code = compile(expr + "\n", "<string %s>" % expr, compile_mode)
    if debug:
        import dis;
        print(dis.dis(code))
    deparsed = code_deparse(code, out=out, compile_mode=compile_mode, debug_opts=debug_opts)
    return deparsed


# FIXME: DRY this code
def test_single_mode() -> None:
    expressions = (
        "1",
        "i and (j or k)",
        "i and j or k",
        "j % 4",
        "i = 1",
        "i += 1",
        "i = j % 4",
        "i = {}",
        "i = []",
        "for i in range(10):\n    i\n",
        "for i in range(10):\n    for j in range(10):\n        i + j\n",
        "(i for i in f if 0 < i < 4)",
        "[i for pair in p if pair for i in f]",
        # Inconsequential differences in spaces.
        # "try:\n    i\nexcept Exception:\n    j\nelse:\n    k",
    )

    for expr in expressions:
        try:
            deparsed = run_deparse(expr, compile_mode="single", debug=False)
        except:
            assert False, expr
            continue

        if deparsed.text != (expr + "\n"):
            from decompyle3.show import maybe_show_tree
            deparsed.showast = {"Full": True}
            maybe_show_tree(deparsed, deparsed.ast)
        assert deparsed.text == expr + "\n"

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
        assert deparsed.text == expr

if __name__ == "__main__":
    test_eval_mode()
    test_lambda_mode()
    test_single_mode()
