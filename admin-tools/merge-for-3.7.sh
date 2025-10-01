#/bin/bash
decompyle3_merge_37_owd=$(pwd)
(cd .. && PYTHON_VERSION=3.7 && pyenv local $PYTHON_VERSION)
cd $(dirname ${BASH_SOURCE[0]})
if . ./setup-python-3.7.sh; then
    git merge master
fi
cd $decompyle3_merge_37_owd
