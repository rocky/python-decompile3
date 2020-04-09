#!/bin/bash

function displaytime {
    printf "ran in "
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

bs=${BASH_SOURCE[0]}
if [[ $0 != $bs ]] ; then
    echo "This script should not be *sourced* but run through bash"
    exit 1
fi

mydir=$(dirname $bs)
cd $mydir

. ../admin-tools/pyenv-versions
MAIN="test_pyenvlib.py"

USER=${USER:-rocky}
EMAIL=${EMAIL:-rb@dustyfeet.com}
WHAT="decompyle3 ${MAIN}"
MAX_TESTS=${MAX_TESTS:-800}
export BATCH=1

typeset -i RUN_STARTTIME=$(date +%s)

MAILBODY=/tmp/${MAIN}-mailbody-$$.txt
for VERSION in $PYVERSIONS ; do
    typeset -i rc=0
    LOGFILE=/tmp/pyenvlib-$VERSION-$$.log

    if [[ $VERSION == '3.7.7' ]] ; then
	# .pyenv/versions/3.7.7/lib/python3.7/__pycache__/compileall.cpython-37.pyc
	# is the first to fail
	# functools fails (needs to parse assert)
	# pydecimal fails. Then we can go to 39
	MAX_TESTS=10
    elif [[ $VERSION == '3.8.2' ]] ; then
	# _compression.cpython-38.pyc fails
	# _markupbase.py.cpython-38.pyc fails
	MAX_TESTS=5
    fi

    if ! pyenv local $VERSION ; then
	rc=1
	mailbody_line="pyenv local $VERSION not installed"
	echo $mailbody_line >> $MAILBODY
    else
      typeset -i ALL_FILES_STARTTIME=$(date +%s)
      cmd="python ./${MAIN} --max ${MAX_TESTS} --syntax-verify --$VERSION"
      echo "$cmd" >>$LOGFILE 2>&1
      $cmd >>$LOGFILE 2>&1
      rc=$?

      echo Python Version $(pyenv local) >> $LOGFILE
      echo "" >>$LOGFILE

      typeset -i ALL_FILES_ENDTIME=$(date +%s)
      (( time_diff =  ALL_FILES_ENDTIME - ALL_FILES_STARTTIME))
      time_str=$(displaytime $time_diff)
      echo $time_str >> $LOGFILE
    fi

    SUBJECT_PREFIX="$WHAT (max $MAX_TESTS) for"
    if ((rc == 0)); then
	mailbody_line="Python $VERSION ok; ${time_str}."
	tail -v $LOGFILE | mail -s "$SUBJECT_PREFIX $VERSION ok" ${USER}@localhost
    else
	mailbody_line="Python $VERSION failed; ${time_str}. Full results in ${LOGFILE}."
	tail -v $LOGFILE | mail -s "$SUBJECT_PREFIX $VERSION not ok" ${USER}@localhost
	tail -v $LOGFILE | mail -s "$HOST $SUBJECT_PREFIX $VERSION not ok" ${EMAIL}
    fi
    echo $mailbody_line >> $MAILBODY
    rm .python-version
done

typeset -i RUN_ENDTIME=$(date +%s)
(( time_diff =  RUN_ENDTIME - RUN_STARTTIME))
elapsed_time=$(displaytime $time_diff)
echo "Run complete in ${elapsed_time}." >> $MAILBODY
cat $MAILBODY | mail -s "$HOST decompyle3 $MAIN finished; ${elapsed_time}." ${EMAIL}
