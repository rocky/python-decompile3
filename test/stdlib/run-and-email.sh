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

source ../../admin-tools/pyenv-versions
RUNTESTS="runtests3.sh"

USER=${USER:-rocky}
EMAIL=${EMAIL:-rb@dustyfeet.com}
WHAT="decompyle3 ${RUNTESTS}"
export BATCH=1

typeset -i RUN_STARTTIME=$(date +%s)

actual_versions=""
DEBUG=""  # -x
MAILBODY=/tmp/${RUNTESTS}-mailbody-$$.txt

for VERSION in $PYVERSIONS ; do
    typeset -i rc=0
    LOGFILE=/tmp/runtests-$VERSION-$$.log

    if ! pyenv local $VERSION ; then
	rc=1
	mailbody_line="pyenv local $VERSION not installed"
	echo $mailbody_line >> $MAILBODY
    else
      typeset -i ALL_FILES_STARTTIME=$(date +%s)
      cmd="/bin/bash ./${RUNTESTS}"
      $cmd >>$LOGFILE 2>&1
      rc=$?

      echo Python Version $(pyenv local) > $LOGFILE
      echo "" >> $LOGFILE

      typeset -i ALL_FILES_ENDTIME=$(date +%s)
      (( time_diff =  ALL_FILES_ENDTIME - ALL_FILES_STARTTIME))
      time_str=$(displaytime $time_diff)
      echo $time_str >> $LOGFILE
    fi

    SUBJECT_PREFIX="$WHAT for"
    if ((rc == 0)); then
	mailbody_line="$WHAT Python $VERSION ok; ${time_str}."
	tail -v $LOGFILE | mail -s "$SUBJECT_PREFIX $VERSION ok" ${USER}@localhost
    else
	mailbody_line="$WHAT Python $VERSION failed. ${time_str}. Full Results in ${LOGFILE}."
	tail -v $LOGFILE | mail -s "$SUBJECT_PREFIX $VERSION not ok" ${USER}@localhost
	tail -v $LOGFILE | mail -s "$SUBJECT_PREFIX $VERSION not ok" ${EMAIL}
    fi
    echo $mailbody_line >> $MAILBODY
    rm .python-version
done

typeset -i RUN_ENDTIME=$(date +%s)
(( time_diff =  RUN_ENDTIME - RUN_STARTTIME))
elapsed_time=$(displaytime $time_diff)
echo "Run complete in ${elapsed_time}." >> $MAILBODY
cat $MAILBODY | mail -s "$HOST decompyle3 ${RUNTESTS} finished; ${elapsed_time}." ${EMAIL}
