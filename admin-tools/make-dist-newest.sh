#!/bin/bash
PACKAGE=decompyle3

# FIXME put some of the below in a common routine
function finish {
  cd $decompyle3_newest_owd
}

cd $(dirname ${BASH_SOURCE[0]})
decompyle3_newest_owd=$(pwd)
trap finish EXIT

if ! source ./pyenv-newest-versions ; then
    exit $?
fi
if ! source ./setup-master.sh ; then
    exit $?
fi

cd ..
source $PACKAGE/version.py
echo $__version__

rm -fr build
pip wheel --wheel-dir=dist .
python -m build --sdist
finish
