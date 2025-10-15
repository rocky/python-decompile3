#!/bin/bash
# The name Python's import uses.
# It is reflected in the directory structure.
PACKAGE_MODULE="decompyle3"

# The name that PyPi sees this as.
# It is set in setup.py's name.
PACKAGE_NAME="decompyle3"
PACKAGE=${PACKAGE_NAME}

# FIXME put some of the below in a common routine
function finish {
  if [[ -n "$decompyle3_37_owd" ]] then
     cd $decompyle3_37_make_owd
  fi
}

decompyle3_37_make_owd=$(pwd)
cd $(dirname ${BASH_SOURCE[0]})
trap finish EXIT

if ! source ./pyenv-3.7-3.10-versions ; then
    exit $?
fi
if ! source ./setup-python-3.7.sh ; then
    exit $?
fi

cd ..
source ./${PACKAGE_MODULE}/version.py
if [[ ! -n $__version__ ]]; then
    echo "Something is wrong: __version__ should have been set."
    exit 1
fi

for pyversion in $PYVERSIONS; do
    case ${pyversion:0:4} in
	"graal" )
	    echo "$pyversion - Graal does not get special packaging"
	    continue
	    ;;
	"jyth" )
	    echo "$pyversion - Jython does not get special packaging"
	    continue
	    ;;
	"pypy" )
	    echo "$pyversion - PyPy does not get special packaging"
	    continue
	    ;;
	"pyst" )
	    echo "$pyversion - Pyston does not get special packaging"
	    continue
	    ;;
    esac
    echo "*** Packaging ${PACKAGE_NAME} for version ${__version__} on Python ${pyversion} ***"

    # pip bdist_egg create too-general wheels. So
    # we narrow that by moving the generated wheel.

    # Pick out first two number of version, e.g. 3.5.1 -> 35
    first_two=$(echo $pyversion | cut -d'.' -f 1-2 | sed -e 's/\.//')
    rm -fr build
    python setup.py bdist_wheel
    mv -v dist/${PACKAGE_MODULE}-$__version__-{py3,py$first_two}-none-any.whl
done

python ./setup.py sdist
tarball=dist/${PACKAGE}-${__version__}.tar.gz

if [[ -f $tarball ]]; then
    version_specific_tarball=dist/${PACKAGE_NAME}_37-${__version__}.tar.gz
    mv -v $tarball $version_specific_tarball
    twine check $version_specific_tarball
fi
twine check dist/${PACKAGE_MODULE}-${__version__}-py3*.whl
finish
