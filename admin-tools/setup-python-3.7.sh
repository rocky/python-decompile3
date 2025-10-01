#!/bin/bash
# Check out git branch python-3.7-to-3.10 and dependent development branches.

PYTHON_VERSION=3.7

bs=${BASH_SOURCE[0]}
if [[ $0 == $bs ]] ; then
    echo "This script should be *sourced* rather than run directly through bash"
    exit 1
fi

decompyle3_owd=$(pwd)
mydir=$(dirname $bs)
cd $mydir
fulldir=$(readlink -f $mydir)
. ./checkout_common.sh
cd $fulldir/..
(cd $fulldir/.. && \
     setup_version python-spark python-3.6 && \
     setup_version python-xdis python-3.6 )

checkout_finish python-3.7-to-3.10
