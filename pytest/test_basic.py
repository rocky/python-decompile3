from xdis.version_info import PythonImplementation

from decompyle3.parsers.main import get_python_parser
from decompyle3.scanner import get_scanner


def test_get_scanner():
    # See that we can retrieve a scanner using a full version number
    assert get_scanner((3, 7, 3), PythonImplementation.CPython)
    assert get_scanner((3, 7, 3), PythonImplementation.PyPy)


def test_get_parser():
    # See that we can retrieve a sparser using a full version number
    assert get_python_parser((3, 7, 3))
