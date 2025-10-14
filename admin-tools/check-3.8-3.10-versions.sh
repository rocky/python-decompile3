#!/bin/bash
function finish {
    if [[ -n ${python_control_flow_owd} ]] && [[ -d $python_control_flow_owd ]]; then
	cd $python_control_flow_owd
    fi
}

# FIXME put some of the below in a common routine
python_control_flow_owd=$(pwd)
# trap finish EXIT

cd $(dirname ${BASH_SOURCE[0]})
if ! source ./pyenv-3.8-3.10-versions ; then
    exit $?
fi

. ./setup-python-3.8.sh

cd ..
for version in $PYVERSIONS; do
    if ! pyenv local $version ; then
	exit $?
    fi
    python --version
    make clean && pip install -e .
    if ! make check; then
	exit $?
    fi
    echo === $version ===
done
