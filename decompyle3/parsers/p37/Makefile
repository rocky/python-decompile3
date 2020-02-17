# Whatever it is you want to do, it should be forwarded to the
# to top-level irectories
PHONY=check all type-check
all: check

MYPYPATH=../../..

#: Static type checking
type-check:
	mypy *.py

%:
	$(MAKE) -C ../../.. $@
