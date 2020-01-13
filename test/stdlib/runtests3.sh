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

STOP_ONERROR=${STOP_ONERROR:-1}

typeset -i timeout=15

function timeout_cmd {

  (
    $@ &
    child=$!
    trap -- "" SIGTERM
    (
	sleep "$timeout"
	if ps -p $child >/dev/null ; then
	    echo ""
	    echo >&1 "**Killing ${2}; takes more than $timeout seconds to run"
	    kill -TERM ${child}
	fi
    ) &
    wait "$child"
  )
}

typeset -A SKIP_TESTS
case $PYVERSION in
    3.7)
	SKIP_TESTS=(
	    [test___all__.py]=1 # it fails on its own
	    [test_argparse.py]=1 #- it fails on its own
	    [test_asdl_parser.py]=1 # it fails on its own
	    [test_ast.py]=1  # Depends on comments in code
	    [test_atexit.py]=1  # The atexit test looks for specific comments in error lines
	    [test_baseexception.py]=1  #
	    [test_bdb.py]=1  #
	    [test_buffer.py]=1  # parse error
	    [test_builtin.py]=1  # parser error
	    [test_clinic.py]=1 # it fails on its own
	    [test_cmath.py]=1 # test assertion failure
 	    [test_cmd_line.py]=1  # Interactive?
	    [test_cmd_line_script.py]=1
	    [test_collections.py]=1
	    [test_compare.py]=1
	    [test_compileall.py]=1 # fails on its own
	    [test_compile.py]=1
	    [test_concurrent_futures.py]=1 # too long
	    [test_configparser.py]=1
	    [test_context.py]=1
	    [test_coroutines.py]=1 # Parse error
	    [test_codecs.py]=1
	    [test_code.py]=1 # Investigate
	    [test_complex.py]=1 # Investigate
	    [test_crypt.py]=1 # Parse error
	    [test_ctypes.py]=1 # it fails on its own
	    [test_curses.py]=1 # Parse error
	    [test_dataclasses.py]=1   # parse error
	    [test_datetime.py]=1   # Takes too long
	    [test_dbm_gnu.py]=1   # Takes too long
	    [test_dbm_ndbm.py]=1 # it fails on its own
	    [test_decimal.py]=1   # Parse error
	    [test_descr.py]=1   # Parse error
	    [test_devpoll.py]=1 # it fails on its own
	    [test_dictcomps.py]=1 # Bad semantics - Investigate
	    [test_dis.py]=1   # We change line numbers - duh!
	    [test_docxmlrpc.py]=1
	    [test_exceptions.py]=1   # parse error
	    [test_enumerate.py]=1   #
	    [test_enum.py]=1   #
	    [test_faulthandler.py]=1   # takes too long
	    [test_fcntl.py]=1
	    [test_fileinput.py]=1
	    [test_float.py]=1
	    [test_format.py]=1
	    [test_frame.py]=1
	    [test_fstring.py]=1 # Investigate
	    [test_ftplib.py]=1
	    [test_functools.py]=1
	    [test_gdb.py]=1 # it fails on its own
	    [test_generators.py]=1  # improper decompile of assert i < n and (n-i) % 3 == 0
	    [test_glob.py]=1  #
	    [test_grammar.py]=1
	    [test_grp.py]=1 # Doesn't terminate (killed)
	    [test_gzip.py]=1 # parse error
	    [test_hashlib.py]=1 # test assert failures
	    [test_http_cookiejar.py]=1
	    [test_httplib.py]=1 # parse error
	    [test_imaplib-3.7.py]=1
	    [test_idle.py]=1 # Probably installation specific
	    [test_io.py]=1 # test takes too long to run: 37 seconds
	    [test_imaplib.py]=1
	    [test_index.py]=1
	    [test_inspect.py]=1
	    [test_itertools.py]=1 # parse error
	    [test_keywordonlyarg.py]=1 # Investigate: parameter handling
	    [test_kqueue.py]=1 # it fails on its own
	    [test_lib2to3.py]=1 # it fails on its own
	    [test_long.py]=1 # investigate
	    [test_logging.py]=1 # test takes too long to run: 20 seconds
	    [test_mailbox.py]=1
	    [test_marshal.py]=1
	    [test_math.py]=1
	    [test_modulefinder.py]=1
	    [test_msilib.py]=1
	    [test_multiprocessing_fork.py]=1 # test takes too long to run: 62 seconds
	    [test_multiprocessing_forkserver.py]=1
	    [test_multiprocessing_spawn.py]=1
	    [test_normalization.py]=1 # probably control flow (uninitialized variable)
	    [test_nntplib.py]=1
	    [test_optparse.py]=1 # doesn't terminate (killed)
	    [test_os.py]=1 # probably control flow (uninitialized variable)
	    [test_ossaudiodev.py]=1 # it fails on its own
	    [test_pathlib.py]=1 # parse error
	    [test_pdb.py]=1 # Probably relies on comments
	    [test_peepholer.py]=1 # test assert error
	    [test_pickle.py]=1 # Probably relies on comments
	    [test_poll.py]=1
	    [test_poplib.py]=1
	    [test_pydoc.py]=1 # it fails on its own
	    [test_runpy.py]=1  #
	    [test_pkg.py]=1 # Investigate: lists differ
	    [test_pkgutil.py]=1 # Investigate:
	    [test_platform.py]=1 # probably control flow: uninitialized variable
	    [test_pow.py]=1 # probably control flow: test assertion failure
	    [test_pwd.py]=1 # killing - doesn't terminate
	    [test_regrtest.py]=1 # lists differ
	    [test_re.py]=1 # test assertion error
	    [test_richcmp.py]=1 # parse error
	    [test_select.py]=1 # test takes too long to run: 11 seconds
	    [test_selectors.py]=1
	    [test_shutil.py]=1 # fails on its own
	    [test_signal.py]=1 #
	    [test_slice.py]=1 # Investigate
	    [test_smtplib.py]=1 #
	    [test_socket.py]=1
	    [test_socketserver.py]=1
	    [test_sort.py]=1 # Probably control flow; unintialized varaible
	    [test_ssl.py]=1 # Probably control flow; unintialized varaible
	    [test_startfile.py]=1 # it fails on its own
	    [test_statistics.py]=1 # Probably control flow; unintialized varaible
	    [test_stat.py]=1 # test assertions failed
	    [test_string_literals.py]=1 # Investigate boolean parsing
	    [test_strptime.py]=1 # test assertions failed
	    [test_strtod.py]=1 # test assertions failed
	    [test_structmembers.py]=1 # test assertions failed
	    [test_struct.py]=1 # test assertions failed
	    [test_subprocess.py]=1
	    [test_sys_setprofile.py]=1 # test assertions failed
	    [test_sys_settrace.py]=1 # parse error
	    [test_tarfile.py]=1 # parse error
	    [test_threading.py]=1 #
	    [test_timeit.py]=1 # probably control flow uninitialized variable
	    [test_tk.py]=1  # test takes too long to run: 13 seconds
	    [test_tokenize.py]=1
	    [test_trace.py]=1  # it fails on its own
	    [test_traceback.py]=1 # Probably uses comment for testing
	    [test_tracemalloc.py]=1 #
	    [test_ttk_guionly.py]=1  # implementation specfic and test takes too long to run: 19 seconds
	    [test_typing.py]=1 # parse error
	    [test_types.py]=1 # parse error
	    [test_unicode.py]=1 # unicode thing
	    [test_urllib2.py]=1 #
	    [test_urllib2_localnet.py]=1 #
	    [test_urllibnet.py]=1 # probably control flow - uninitialized variable
	    [test_weakref.py]=1 # probably control flow - uninitialized variable
	    [test_with.py]=1 # probably control flow - uninitialized variable
	    [test_xml_dom_minicompat.py]=1 # parse error
	    [test_winconsoleio.py]=1 # it fails on its own
	    [test_winreg.py]=1 # it fails on its own
	    [test_winsound.py]=1 # it fails on its own
	    [test_zipfile.py]=1 # it fails on its own
	    [test_zipfile64.py]=1 #
	    )
	    # 268 Remaining unit-test files, Elapsed time about 11 minutes
	;;
    3.8)
	SKIP_TESTS=(
	    [test_ast.py]=1  # parse error and then Depends on comments in code
	    [test_aifc.py]=1  # parse error
	    [test_argparse.py]=1  # parse error
	    [test_asyncgen.py]=1  # parse error
	    [test_asynchat.py]=1  # parse error
	    [test_atexit.py]=1  # The atexit test looks for specific comments in error lines
	    [test_audiop.py]=1  # parse error
	    [test_audit.py]=1  # parse error
	    [test_bool.py]=1 # parse error
	    [test_buffer.py]=1 # parse error
	    [test_cmath.py]=1  # parse error
	    [test_collections.py]=1  # Investigate
	    [test_decorators.py]=1  # Control flow wrt "if elif"
	    [test_exceptions.py]=1   # parse error
	    [test_dis.py]=1   # We change line numbers - duh!
	    [test_fileio.py]=1   # parse error
	    [test_pow.py]=1         # Control flow wrt "continue"
	    [test_quopri.py]=1      # Only fails on POWER
	    # ...
	)
	;;
    *)
	SKIP_TESTS=( [test_aepack.py]=1
		     [audiotests.py]=1
		     [test_dis.py]=1   # We change line numbers - duh!
		     [test_generators.py]=1  # I think string formatting of docstrings gets in the way. Not sure
		   )
	;;
esac

# Test directory setup
srcdir=$(dirname $me)
cd $srcdir
fulldir=$(pwd)

# pyenv version cleaning
for dir in .. ../.. ; do
    (cd $dir && [[ -r .python-version ]] && rm -v .python-version )
done

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
    if [ ! -r $file ]; then
	echo "Skipping test $file -- not readable. Does it exist?"
	continue
    elif ! python $file >/dev/null 2>&1 ; then
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
    # (( i > 40 )) && break
    short_name=$(basename $file .py)
    decompiled_file=$short_name-${PYVERSION}.pyc
    $fulldir/compile-file.py $file && \
    mv $file{,.orig} && \
    echo ==========  $(date +%X) Decompiling $file ===========
    $DECOMPILER $decompiled_file > $file
    rc=$?
    if (( rc == 0 )) ; then
	echo ========== $(date +%X) Running $file ===========
	timeout_cmd python $file
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

printf "Ran $i unit-test files, $allerrs errors; Elapsed time: "
displaytime $time_diff
echo "Skipped $skipped test for known failures."
cd $fulldir/../.. && pyenv local $FULLVERSION
exit $allerrs
