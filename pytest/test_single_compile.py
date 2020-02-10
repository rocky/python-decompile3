from decompyle3 import code_deparse


def test_single_mode():
    single_expressions = (
        "i = 1",
        "i and (j or k)",
        "i += 1",
        "i = j % 4",
        "i = {}",
        "i = []",
        "for i in range(10):\n    i\n",
        "for i in range(10):\n    for j in range(10):\n        i + j\n",
        # "try:\n    i\nexcept Exception:\n    j\nelse:\n    k\n"
    )

    for expr in single_expressions:
        code = compile(expr + "\n", "<string>", "single")
        assert code_deparse(code, compile_mode="single").text == expr + "\n"

if __name__ == "__main__":
    test_single_mode()
