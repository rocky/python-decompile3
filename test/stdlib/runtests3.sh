#!/bin/bash
me=${BASH_SOURCE[0]}

typeset -i batch=1
isatty=$(/usr/bin/tty 2>/dev/null)
if [[ -n $isatty ]] && [[ "$isatty" != 'not a tty' ]] ; then
    batch=0
fi


function displaytime {
  local T=$1
  local D=$((T/60/60/24))
  local H=$((T/60/60%24))
  local M=$((T/60%60))
  local S=$((T%60))
  (( $D > 0 )) && printf '%d days ' $D
  (( $H > 0 )) && printf '%d hours ' $H
  (( $M > 0 )) && printf '%d minutes ' $M
  (( $D > 0 || $H > 0 || $M > 0 )) && printf 'and '
  printf '%d seconds\n' $S
}

# Python version setup
FULLVERSION=$(pyenv local)
PYVERSION=${FULLVERSION%.*}
MINOR=${FULLVERSION##?.?.}

typeset -i STOP_ONERROR=0

typeset -A SKIP_TESTS
case $PYVERSION in
    3.7)
	SKIP_TESTS=(
	    [test_ast.py]=1  # test assertion error
	    [test_atexit.py]=1  #
	    [test_baseexception.py]=1  #
	    [test_bdb.py]=1  #
	    [test_buffer.py]=1  # parse error
	    [test_cmd_line.py]=1  # Interactive?
	    [test_cmd_line_script.py]=1
	    [test_collections.py]=1
	    [test_compare.py]=1
	    [test_compile.py]=1
	    [test_configparser.py]=1
	    [test_contextlib_async.py]=1 # Investigate
	    [test_context.py]=1
	    [test_coroutines.py]=1 # Parse error
	    [test_crypt.py]=1 # Parse error
	    [test_curses.py]=1 # Parse error
	    [test_dataclasses.py]=1   # parse error
	    [test_datetime.py]=1   # Takes too long
	    [test_dbm_gnu.py]=1   # Takes too long
	    [test_decimal.py]=1   # Parse error
	    [test_descr.py]=1   # Parse error
	    [test_dictcomps.py]=1 # Bad semantics - Investigate
	    [test_dis.py]=1   # We change line numbers - duh!
	    [test_enumerate.py]=1   #
	    [test_enum.py]=1   #
	    [test_faulthandler.py]=1   # takes too long
	    [test_generators.py]=1  # improper decompile of assert i < n and (n-i) % 3 == 0
	    # ...
	)
	if (( batch )) ; then
	    # Fails in crontab environment?
	    # Figure out what's up here
	    SKIP_TESTS[test_exception_variations.py]=1
	    SKIP_TESTS[test_quopri.py]=1
	fi
	;;

    3.8)
	SKIP_TESTS=(
	    [test_collections.py]=1  # parse error
	    [test_decorators.py]=1  # Control flow wrt "if elif"
	    [test_dis.py]=1   # We change line numbers - duh!
	    [test_generators.py]=1  # Investigate
	    [test_pow.py]=1         # Control flow wrt "continue"
	    [test_quopri.py]=1      # Only fails on POWER
	    # ...
	)
	;;
    *)
	SKIP_TESTS=( [test_aepack.py]=1
		     [audiotests.py]=1
		     [test_dis.py]=1   # We change line numbers - duh!
		   )
	;;
esac

# Test directory setup
srcdir=$(dirname $me)
cd $srcdir
fulldir=$(pwd)

DECOMPILER=${DECOMPILER:-"$fulldir/../../bin/decompyle3"}
TESTDIR=/tmp/test${PYVERSION}
if [[ -e $TESTDIR ]] ; then
    rm -fr $TESTDIR
fi

PYENV_ROOT=${PYENV_ROOT:-$HOME/.pyenv}
pyenv_local=$(pyenv local)
mkdir $TESTDIR || exit $?
cp -r ${PYENV_ROOT}/versions/${PYVERSION}.${MINOR}/lib/python${PYVERSION}/test $TESTDIR
cd $TESTDIR/test
pyenv local $FULLVERSION
export PYTHONPATH=$TESTDIR
export PATH=${PYENV_ROOT}/shims:${PATH}

# Run tests
typeset -i i=0
typeset -i allerrs=0
if [[ -n $1 ]] ; then
    files=$1
    typeset -a files_ary=( $(echo $1) )
    if (( ${#files_ary[@]} == 1 )) ; then
	SKIP_TESTS=()
    fi
else
    files=$(echo test_*.py)
fi

typeset -i ALL_FILES_STARTTIME=$(date +%s)
typeset -i skipped=0

for file in $files; do
    # AIX bash doesn't grok [[ -v SKIP... ]]
    if [[ ${SKIP_TESTS[$file]} == 1 ]] ; then
	((skipped++))
	continue
    fi

    # If the fails *before* decompiling, skip it!
    typeset -i STARTTIME=$(date +%s)
    if ! python $file >/dev/null 2>&1 ; then
	echo "Skipping test $file -- it fails on its own"
	continue
    fi
    typeset -i ENDTIME=$(date +%s)
    typeset -i time_diff
    (( time_diff =  ENDTIME - STARTTIME))
    if (( time_diff > 10 )) ; then
	echo "Skipping test $file -- test takes too long to run: $time_diff seconds"
	continue
    fi

    ((i++))
    (( i > 20 )) && break
    short_name=$(basename $file .py)
    decompiled_file=$short_name-${PYVERSION}.pyc
    $fulldir/compile-file.py $file && \
    mv $file{,.orig} && \
    echo ==========  $(date +%X) Decompiling $file ===========
    $DECOMPILER $decompiled_file > $file
    rc=$?
    if (( rc == 0 )) ; then
	echo ========== $(date +%X) Running $file ===========
	python $file
	rc=$?
    else
	echo ======= Skipping $file due to compile/decompile errors ========
    fi
    (( rc != 0 && allerrs++ ))
    if (( STOP_ONERROR && rc )) ; then
	echo "** Ran $i tests before failure. Skipped $skipped test for known failures. **"
	exit $allerrs
    fi
done
typeset -i ALL_FILES_ENDTIME=$(date +%s)

(( time_diff =  ALL_FILES_ENDTIME - ALL_FILES_STARTTIME))

printf "Ran $i unit-test files in "
displaytime $time_diff
echo "Failed tests $allerrs; skipped $skipped test for known failures."

exit $allerrs
