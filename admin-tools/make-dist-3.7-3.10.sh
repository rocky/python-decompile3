#!/bin/bash
PACKAGE=decompyle3

# FIXME put some of the below in a common routine
function finish {
  cd $decompyle3_37_make_owd
}

cd $(dirname ${BASH_SOURCE[0]})
decompyle3_37_make_owd=$(pwd)
trap finish EXIT

if ! source ./pyenv-3.7-3.10-versions ; then
    exit $?
fi
# if ! source ./setup-python-3.7.sh ; then
#     exit $?
# fi

cd ..
source $PACKAGE/version.py
echo $__version__

for pyversion in $PYVERSIONS; do
    echo --- $pyversion ---
    if [[ ${pyversion:0:4} == "pypy" ]] ; then
	echo "$pyversion - PyPy does not get special packaging"
	continue
    fi
    if ! pyenv local $pyversion ; then
	exit $?
    fi
    if [[ ${pyversion:0:6} == "pyston" ]] ; then
	echo "$pyversion - Pyston does not get special packaging"
	continue
    fi
    # pip bdist_egg create too-general wheels. So
    # we narrow that by moving the generated wheel.

    # Pick out first two number of version, e.g. 3.5.1 -> 35
    first_two=$(echo $pyversion | cut -d'.' -f 1-2 | sed -e 's/\.//')
    rm -fr build
    python setup.py bdist_egg bdist_wheel
    mv -v dist/${PACKAGE}-$__version__-{py3,py$first_two}-none-any.whl
    echo === $pyversion ===
done

python ./setup.py sdist
tarball=dist/${PACKAGE}-${__version__}.tar.gz
if [[ -f $tarball ]]; then
    mv -v $tarball dist/${PACKAGE}_37-${__version__}.tar.gz
fi
finish
