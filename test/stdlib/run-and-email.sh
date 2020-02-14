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
SUBJECT_PREFIX="stdlib unit testing for"
export BATCH=1

typeset -i RUN_STARTTIME=$(date +%s)

actual_versions=""
DEBUG=""  # -x
MAILBODY=/tmp/runtests-mailbody-$$.txt

for VERSION in $PYVERSIONS ; do
    typeset -i rc=0
    LOGFILE=/tmp/runtests-$VERSION-$$.log

    if ! pyenv local $VERSION ; then
	rc=1
    else
      /bin/bash ./${RUNTESTS}  >$LOGFILE 2>&1
      rc=$?
    fi
    typeset -i RUN_ENDTIME=$(date +%s)
    (( time_diff =  RUN_ENDTIME - RUN_STARTTIME))
    elapsed_time=$(displaytime $time_diff)
    echo $elaped_time >> $LOGFILE
    mailbody_line="Python $VERSION ran in $elapsed_time"
    if ((rc == 0)); then
	mailbody_line="$mailbody_line ok"
	tail -v $LOGFILE | mail -s "$SUBJECT_PREFIX $VERSION ok" ${USER}@localhost
    else
	mailbody_line="$mailbody_line failed"
	tail -v $LOGFILE | mail -s "$SUBJECT_PREFIX $VERSION not ok" ${USER}@localhost
	tail -v $LOGFILE | mail -s "$SUBJECT_PREFIX $VERSION not ok" $EMAIL
    fi
    echo $mailbody_line >> $MAILBODY
done

typeset -i RUN_ENDTIME=$(date +%s)
(( time_diff =  RUN_ENDTIME - RUN_STARTTIME))
elapsed_time=$(displaytime $time_diff)
echo "Run complete in $elapsed_time" >> $MAILBODY
cat $MAILBODY | mail -s "$HOST decompyle3 ${RUNTESTS} finished in $elapsed_time" ${EMAIL}
