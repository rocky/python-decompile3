#!/bin/bash
# Remake Python grammar statistics

typeset -A ALL_VERS=([3.7]=3.7.3)

if (( $# == 0 )); then
    echo 1>&2 "usage: $0 two-digit-version"
    exit 1
fi

me=${BASH_SOURCE[0]}
workdir=$(dirname $me)
cd $workdir
workdir=$(pwd)
while [[ -n $1 ]]  ; do
    SHORT_VERSION=$1; shift
    LONG_VERSION=${ALL_VERS[$SHORT_VERSION]}
    if [[ -z ${LONG_VERSION} ]] ; then
       echo 1>&2 "Version $SHORT_VERSION not known"
       exit 2
    fi

    tmpdir=$workdir/../../tmp/grammar-cover
    COVER_FILE=${tmpdir}/spark-grammar-${SHORT_VERSION}.cover
    [[ -d  $tmpdir ]] || mkdir $tmpdir
    cd $workdir/../..
    GRAMMAR_TXT=$tmpdir/grammar-${SHORT_VERSION}.txt
    (cd ../.. && pyenv local ${LONG_VERSION})
    cd ./test
    if [[ -r $COVER_FILE ]]; then
	rm $COVER_FILE
    fi
    if [[ -r $GRAMMAR_TXT ]]; then
        GRAMMAR_SAVE_TXT=${tmpdir}/grammar-${SHORT_VERSION}-save.txt
        cp $GRAMMAR_TXT $GRAMMAR_SAVE_TXT
    fi
    make grammar-coverage-${SHORT_VERSION};
    spark-parser-coverage --max-count=3000 --path $COVER_FILE > $GRAMMAR_TXT
done
