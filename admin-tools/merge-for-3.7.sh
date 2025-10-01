#/bin/bash
PYTHON_VERSION=3.7
decompyle3_merge_37_owd=$(pwd)
cd $(dirname ${BASH_SOURCE[0]})
(cd .. && pyenv local $PYTHON_VERSION)
if . ./setup-python-3.7.sh; then
    git merge master
fi
cd $decompyle3_merge_37_owd
