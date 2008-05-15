#!/bin/sh
usage() { (cat <<USAGE
Build and upload binary and source distributions.
Usage: $0 [options] [python ...]
Options:
 -s         Do not include source.
 -b         Do not build or include binaries.
 -u         Upload all packages in ./dist/ to PyPI and smisk/dists.
 -v         Verbose (disabled --quiet in setup.py)
 -vv        Very verbose (enables --verbose in setup.py)
 -h/--help  Display help and exit.
USAGE
  ) >&2
}

#----------------------------------------------------------------------------
# Options

cd "$(dirname "$0")/.."
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then usage ; exit 1; fi

DIST_SOURCE=1
DIST_BINARY=1
UPLOAD=0
PYTHONS=
DEFAULT_PYTHON=$(which python)
VERBOSE_V=
VERBOSE_SETUP_PY=
QUIET_SETUP_PY='--quiet'

while getopts 'sbuvh' OPTION; do
  case $OPTION in
    s)  DIST_SOURCE=0 ;;
    b)  DIST_BINARY=0 ;;
    u)  UPLOAD=1 ;;
    v)  VERBOSE_V='-v' ;
        if [ -z $QUIET_SETUP_PY ]; then
          # 2nd time -v appears
          VERBOSE_SETUP_PY='--verbose'
        fi
        QUIET_SETUP_PY= ;
      ;;
    *)  usage ; exit 2 ;;
  esac
done
shift $(($OPTIND - 1))

#----------------------------------------------------------------------------
# Python interpreters

# Some options need python binaries
if [ $DIST_BINARY -eq 1 ] && [ $# -eq 0 ]; then
  # "python" must be last in this list:
  for n in python2.4 python2.5 python; do
    np=$(which "$n")
    if [ -n $np ] && ($np -V 2>/dev/null); then
      if [ "$n" = "python" ] && [ "$PYTHONS" = "" ]; then
        # only add python if no pythonX.X was found or we get duplicates
        PYTHONS="$PYTHONS$np "
      elif [ $n != "python" ]; then
        PYTHONS="$PYTHONS$np "
      fi
    fi
  done
  if [ "$PYTHONS" = "" ]; then
    if [ "$DEFAULT_PYTHON" != "" ]; then
      PYTHONS="$DEFAULT_PYTHON"
    else
      echo "$0: Error: no python interpreters specified and none found." >&2
      usage ; exit 3
    fi
  fi
else
  PYTHONS="$@"
fi

#----------------------------------------------------------------------------
# Main

if [ $DIST_BINARY -eq 1 ] || [ $DIST_SOURCE -eq 1 ]; then

  rm $VERBOSE_V -rf dist/* || exit 1
  rm $VERBOSE_V -rf doc/api || exit 1

  if [ $DIST_BINARY -eq 1 ]; then
    for PYTHON in $PYTHONS; do
      PY_VER=$($PYTHON -V 2>&1)
      if ! (echo "$PY_VER" | grep 'Python' 2>&1 >/dev/null); then
        echo "$0: $PYTHON does not appear to be a Python interpreter -- skipping"
        continue
      fi
      PY_VER="$(echo "$PY_VER" | sed 's/[^0-9\.]//g' | cut -d . -f 1,2)"
      echo "Building for Python $PY_VER using $PYTHON"
      
      # Force a clean build
      rm $VERBOSE_V -rf build/* || exit 1
      
      # Build binary egg
      $PYTHON setup.py $VERBOSE_SETUP_PY $QUIET_SETUP_PY bdist_egg || exit 1
      # smisk-M.m.b[tag]-pyM.m-system-arch.egg
      # smisk-1.0.1dev-py2.5-macosx-10.3-i386.egg
      
      # Build binary archive
      $PYTHON setup.py $VERBOSE_SETUP_PY $QUIET_SETUP_PY bdist --formats=gztar --dist-dir=dist/bdist-py$PY_VER || exit 1
      N=$(cd dist/bdist-py$PY_VER && echo *.tar.gz)
      V="$($DEFAULT_PYTHON setup.py --version | cut -d. -f 1,2).$(echo $N | cut -d. -f 3)"
      NN=$(echo $N | sed 's/smisk-'$V'./smisk-'$V'-py'$PY_VER'-/')
      mv $VERBOSE_V dist/bdist-py$PY_VER/$N dist/$NN
      rm $VERBOSE_V -r dist/bdist-py$PY_VER
      # smisk-M.m.b[tag]-pyM.m-system-arch.tar.gz
      # smisk-1.0.1dev-py2.5-macosx-10.3-i386.tar.gz
      
    done
  fi

  if [ $DIST_SOURCE -eq 1 ]; then
    echo "Creating source package"
    # Build source archive
    $DEFAULT_PYTHON setup.py $VERBOSE_SETUP_PY $QUIET_SETUP_PY sdist || exit 1
    # smisk-M.m.b[tag].tar.gz
    # smisk-1.0.1dev.tar.gz
  fi
  
fi

if [ $UPLOAD -eq 1 ]; then
  $DEFAULT_PYTHON setup.py $VERBOSE_SETUP_PY upload --sign --identity=rasmus --show-response || exit 1
fi

exit 0