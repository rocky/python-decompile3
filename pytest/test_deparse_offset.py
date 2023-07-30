from io import StringIO

from decompyle3.semantics.pysource import deparse_code2str


# Some simple function to decompile
def assign_stmts():
    a = 1
    b = 2
    c = 3
    return a + b + c


def test_assign_stmts_with_offset():
    code = assign_stmts.__code__
    out = StringIO()
    deparsed_text = deparse_code2str(code, out)
    assert deparsed_text == "a = 1\nb = 2\nc = 3\nreturn a + b + c\n"
    out = StringIO()
    deparsed_text = deparse_code2str(code, out, start_offset=4)
    assert deparsed_text == "b = 2\nc = 3\nreturn a + b + c\n"
