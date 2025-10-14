#!/usr/bin/bash
PACKAGE_MODULE=decompyle3
decompyle3_owd=$(pwd)
bs=${BASH_SOURCE[0]}
mydir=$(dirname $bs)
decompyle3_fulldir=$(readlink -f $mydir)
cd $decompyle3_fulldir
. ./checkout_common.sh

pyenv_file="pyenv-3.7-3.10-versions"
if ! source $pyenv_file ; then
    echo "Having trouble reading ${pyenv_file} version $(pwd)"
    exit 1
fi

source ../${PACKAGE_MODULE}/version.py
if [[ ! $__version__ ]] ; then
    echo "Something is wrong: __version__ should have been set."
    exit 1
fi

cd ../dist/

install_file="python-control-flow_37-${__version__}.tar.gz"
install_check_command="python-cfg --version"
for version in $PYVERSIONS; do
    echo "*** Installing ${install_file} for Python ${version} ***"
    echo $version
    pyenv local $version
    pip install $install_file
    $install_check_command
    echo "----"
done
