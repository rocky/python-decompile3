PHONY=check clean dist distclean test test-unit test-functional rmChangeLog clean_pyc nosetests \
      check-bytecode-1  check-bytecode-1.3 check-bytecode-1.4 check-bytecode-1.5 \
      check-bytecode-2 check-bytecode-3 check-bytecode-3-short \
      check-bytecode-2.2 check-byteocde-2.3 check-bytecode-2.4 \
      check-short check-2.6 check-2.7 check-3.0 check-3.1 check-3.2 check-3.3 \
      check-3.4 check-3.5 check-3.6 check-3.7 check-5.6 5.6 5.8 \
      grammar-coverage-3.7

GIT2CL ?= git2cl
PYTHON ?= python

PYTHON_VERSION = $(shell $(PYTHON) -V 2>&1 | cut -d ' ' -f 2 | cut -d'.' -f1,2)
NATIVE_CHECK = check-$(PYTHON_VERSION)

# Set COMPILE='--compile' to force compilation before check
COMPILE ?=
COVER_DIR=../tmp/grammar-cover

# Run short tests
check-short:
	@$(PYTHON) -V && PYTHON_VERSION=`$(PYTHON) -V 2>&1 | cut -d ' ' -f 2 | cut -d'.' -f1,2`; \
	$(MAKE) check-bytecode-$${PYTHON_VERSION}

# Run all tests
check:
	$(PYTHON) -V && PYTHON_VERSION=`$(PYTHON) -V 2>&1 | cut -d ' ' -f 2 | cut -d'.' -f1,2`; \
	$(MAKE) check-$(PYTHON_VERSION)

#: Run working tests from Python 3.7
check-3.7: check-bytecode
	$(PYTHON) test_pythonlib.py --bytecode-3.7-run --verify-run
	$(PYTHON) test_pythonlib.py --bytecode-3.7 --syntax-verify $(COMPILE)

#: Run working tests from Python 3.8
check-3.8: check-bytecode
	$(PYTHON) test_pythonlib.py --bytecode-3.8-run --verify-run
	$(PYTHON) test_pythonlib.py --bytecode-3.8 --syntax-verify $(COMPILE)

#: Check deparsing bytecode 3.x only
check-bytecode-3:
	$(PYTHON) test_pythonlib.py \
	--bytecode-3.7 --bytecode-3.8

#: Check deparsing bytecode on all Python 2 and Python 3 versions
check-bytecode: check-bytecode-3


#: Get grammar coverage for Python 3.7
grammar-coverage-3.7:
	rm $(COVER_DIR)/spark-grammar-3.7.cover || /bin/true
	SPARK_PARSER_COVERAGE=$(COVER_DIR)/spark-grammar-3.7.cover $(PYTHON) test_pythonlib.py --bytecode-3.7-run --verify-run
	SPARK_PARSER_COVERAGE=$(COVER_DIR)/spark-grammar-3.7.cover $(PYTHON) test_pythonlib.py --bytecode-3.7 --syntax-verify $(COMPILE)
	SPARK_PARSER_COVERAGE=$(COVER_DIR)/spark-grammar-3.7.cover $(PYTHON) test_pyenvlib.py --3.7.3 --max=1000

#: Check deparsing Python 3.7
check-bytecode-3.7:
	$(PYTHON) test_pythonlib.py --bytecode-3.7-run --verify-run
	$(PYTHON) test_pythonlib.py --bytecode-3.7 --syntax-verify

#: Check deparsing Python 3.8
check-bytecode-3.8:
	$(PYTHON) test_pythonlib.py --bytecode-3.8-run --verify-run
	$(PYTHON) test_pythonlib.py --bytecode-3.8 --syntax-verify

clean: clean-py-dis clean-dis clean-unverified

clean-dis:
	find . -name '*_dis' -exec rm -v '{}' ';'

clean-unverified:
	find . -name '*_unverified' -exec rm -v '{}' ';'

#: Clean temporary compile/decompile/verify directories in /tmp
clean-py-dis:
	rm -fr /tmp/py-dis-* || true
