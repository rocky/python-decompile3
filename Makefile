# Compatibility for us old-timers.

# Note: This makefile include remake-style target comments.
# These comments before the targets start with #:
# remake --tasks to shows the targets and the comments

GIT2CL ?= git2cl
PYTHON ?= python
PYTHON3 ?= python3
RM      ?= rm
LINT    = flake8

IS_PYPY = $(shell $(PYTHON) -c 'import platform; print("pypy" if platform.python_implementation() == "PyPy" else "")')
PYTHON_VERSION = $(shell $(PYTHON) -V 2>&1 | cut -d ' ' -f 2 | cut -d'.' -f1,2 | head -1)$(IS_PYPY)

#EXTRA_DIST=ipython/ipy_trepan.py trepan
PHONY=all test check clean distcheck pytest check-long dist distclean lint flake8 test rmChangeLog clean_pyc

TEST_TYPES=check-long check-short

#: Default target - same as "check"
all: check

#: Run all tests
test check:
	$(MAKE) check-$(PYTHON_VERSION)

#: Run all quick tests
check-short: pytest
	$(MAKE) -C test check-short

check-3.7 check-3.8: pytest
	PYTHONLIB_OPTS="--run --verify-run" $(MAKE) -C test check

check-3.9 check-3.10 check-3.11 check-3.12 check-3.13: pytest
	$(MAKE) -C test check-bytecode-3.7

check-3.9 check-3.10: pytest

#: Run working tests from Python 3.8
check-3.8pypy:
	$(MAKE) -C test $@


# FIXME
#: pypy3.8-7.3.7
7.3:

#: pyston 3.8-2.3.3
2.3:

#: Run py.test tests
pytest:
	$(MAKE) -C pytest check

#: Clean up temporary files and .pyc files
clean: clean_pyc
	(cd test && $(MAKE) clean)

#: Remove .pyc files
clean_pyc:
	( cd decompyle3 && $(RM) -f *.pyc */*.pyc )

#: Create source tarball
sdist:
	$(PYTHON) ./setup.py sdist


#: Static type checking
type-check:
	mypy decompyle3

#: Style check. Set env var LINT to pyflakes, flake, or flake8
lint: flake8

# Check StructuredText long description formatting
check-rst:
	$(PYTHON) setup.py --long-description | rst2html.py > python3-trepan.html

#: Lint program
flake8:
	$(LINT) decompyle3

#: Create binary egg distribution
bdist_egg:
	$(PYTHON) ./setup.py bdist_egg


#: Create binary wheel distribution
wheel:
	$(PYTHON) ./setup.py bdist_wheel


# It is too much work to figure out how to add a new command to distutils
# to do the following. I'm sure distutils will someday get there.
DISTCLEAN_FILES = build dist *.pyc

#: Remove ALL derived files
distclean: clean
	-rm -fvr $(DISTCLEAN_FILES) || true
	-find . -name \*.pyc -exec rm -v {} \;
	-find . -name \*.egg-info -exec rm -vr {} \;

#: Install package locally
verbose-install:
	$(PYTHON) ./setup.py install

#: Install package locally without the verbiage
install:
	$(PYTHON) ./setup.py install >/dev/null

rmChangeLog:
	rm ChangeLog || true

#: Create a ChangeLog from git via git log and git2cl
ChangeLog: rmChangeLog
	git log --pretty --numstat --summary | $(GIT2CL) >$@
	patch ChangeLog < ChangeLog-spell-corrected.diff

.PHONY: $(PHONY)
