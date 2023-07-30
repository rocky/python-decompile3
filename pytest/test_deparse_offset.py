"""
Tests test deparse_code2str using start_offset and end_offset parameters.

Much of the code here is the same as using decompyle3 using using the
--start-offset and --end--offset options.

"""
from io import StringIO

from xdis.version_info import IS_PYPY, PYTHON_VERSION_TRIPLE

from decompyle3.code_fns import disco_deparse
from decompyle3.semantics.pysource import DEFAULT_DEBUG_OPTS, deparse_code2str


# Some simple function to decompile
def assign_stmts():
    a = 1
    b = 2
    c = 3
    return a + b + c


lambda_fn = lambda a: 5 if a else 6  # noqa


def test_assign_stmts_with_offset():
    assign_code = assign_stmts.__code__
    out = StringIO()
    deparsed_text = deparse_code2str(assign_code, out)
    assert deparsed_text == "a = 1\nb = 2\nc = 3\nreturn a + b + c\n"

    out = StringIO()
    deparsed_text = deparse_code2str(assign_code, out, start_offset=4)
    assert deparsed_text == "b = 2\nc = 3\nreturn a + b + c\n"

    out = StringIO()
    ifelse_code = lambda_fn.__code__
    disco_deparse(
        PYTHON_VERSION_TRIPLE,
        co=ifelse_code,
        codename_map={"<lambda>": "lambda"},
        out=out,
        is_pypy=IS_PYPY,
        debug_opts=DEFAULT_DEBUG_OPTS,
    )
    last_line = out.getvalue().split("\n")[-1]
    assert last_line == "5 if a else 6"

    out = StringIO()
    ifelse_code = lambda_fn.__code__
    disco_deparse(
        PYTHON_VERSION_TRIPLE,
        co=ifelse_code,
        codename_map={"<lambda>": "lambda"},
        out=out,
        is_pypy=IS_PYPY,
        debug_opts=DEFAULT_DEBUG_OPTS,
        start_offset=4,
        stop_offset=8,
    )
    last_line = out.getvalue().split("\n")[-1]
    assert last_line == "5"

    out = StringIO()
    ifelse_code = lambda_fn.__code__
    disco_deparse(
        PYTHON_VERSION_TRIPLE,
        co=ifelse_code,
        codename_map={"<lambda>": "lambda"},
        out=out,
        is_pypy=IS_PYPY,
        debug_opts=DEFAULT_DEBUG_OPTS,
        start_offset=8,
    )
    last_line = out.getvalue().split("\n")[-1]
    assert last_line == "6"
