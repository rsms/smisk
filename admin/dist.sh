#!/bin/sh
REMOTE_HOST='trac.hunch.se'
REMOTE_PATH='/var/lib/trac/smisk/dist/'
REMOTE_PATH_DOCS='/var/lib/trac/smisk/docs/'
#----------------------------------------------------------------------------
usage() { (cat <<USAGE
Build and upload binary and source distributions.
Usage: $0 [options] [python ...]
Options:
 -s         Do not include source.
 -b         Do not build or include binaries.
 -u         Upload all packages in ./dist/ matching *.tar.gz and *.egg. No
            effect if both -s and -b is specified.
 -v         Verbose (disables --quiet in setup.py)
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
UPLOAD_CHECKSUMS=1
UPLOAD_SIGN=1
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

if [ "$VERBOSE_V" = "-v" ]; then
  alias v_echo=echo
else
  alias v_echo=true
fi

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
# Helpers

GPG_PASSP_TMP="$HOME/.gnupg/passphrase.tmp"
GPG_FLAGS=
GPG_INITED=0

gpg_init() {
  if [ $GPG_INITED -eq 0 ]; then
    rm -rf "$GPG_PASSP_TMP"
    touch "$GPG_PASSP_TMP"
    chmod 0600 "$GPG_PASSP_TMP"
    # using GPG_FLAGS for temporary storage. xxx can we make this safer by _not_ storing + echoing?
    echo 'Enter GPG pass phrase for unlocking your secret key' >&2
    read -rsp '(Empty answer to have GPG ask for it in a more scure way for every file): ' GPG_FLAGS
    echo
    if [ "$GPG_FLAGS" != "" ]; then
      echo "$GPG_FLAGS" > "$GPG_PASSP_TMP"
      GPG_FLAGS="--no-verbose --quiet --batch --no-tty --passphrase-file $GPG_PASSP_TMP"
    else
      GPG_FLAGS=
    fi
  fi
}

gpg_finalize() {
  rm -rf "$GPG_PASSP_TMP"
}


#----------------------------------------------------------------------------
# Main

if [ $DIST_BINARY -eq 1 ] || [ $DIST_SOURCE -eq 1 ]; then
  # SETUP_UPLOAD=
  # if [ $UPLOAD -eq 1 ]; then
  #   SETUP_UPLOAD="upload --sign --show-response"
  #   gpg_init
  # fi
  
  rm $VERBOSE_V -rf dist || exit 1
  rm $VERBOSE_V -rf doc/api || exit 1
  
  FILES_CREATED="dist/*.tar.gz"
  
  if [ $DIST_SOURCE -eq 1 ]; then
    echo "Creating source package"
    # Build source archive
    $DEFAULT_PYTHON setup.py $VERBOSE_SETUP_PY $QUIET_SETUP_PY sdist || exit 1
    # smisk-M.m.b[tag].tar.gz
    # smisk-1.0.1dev3.tar.gz
  fi

  if [ $DIST_BINARY -eq 1 ]; then
    for PYTHON in $PYTHONS; do
      PY_VER=$($PYTHON -V 2>&1)
      if ! (echo "$PY_VER" | grep 'Python' 2>&1 >/dev/null); then
        echo "$0: $PYTHON does not appear to be a Python interpreter -- skipping"
        continue
      fi
      PY_VER="$(echo "$PY_VER" | sed 's/[^0-9\.]//g' | cut -d . -f 1,2)"
      echo "Building for Python $PY_VER"
      v_echo "using $PYTHON"
      
      # Force a clean build
      rm $VERBOSE_V -rf build/* || exit 1
      
      # Build binary egg
      $PYTHON setup.py $VERBOSE_SETUP_PY $QUIET_SETUP_PY bdist_egg || exit 1
      # smisk-M.m.b[tag]-pyM.m-system-arch.egg
      # smisk-1.0.1dev3-py2.5-macosx-10.3-i386.egg
      
      # Build binary archive
      $PYTHON setup.py $VERBOSE_SETUP_PY $QUIET_SETUP_PY bdist --formats=gztar --dist-dir=dist/bdist-py$PY_VER || exit 1
      N=$(cd dist/bdist-py$PY_VER && echo *.tar.gz)
      V="$($DEFAULT_PYTHON setup.py --version | cut -d. -f 1,2).$(echo $N | cut -d. -f 3)"
      NN=$(echo $N | sed 's/smisk-'$V'./smisk-'$V'-py'$PY_VER'-/')
      mv $VERBOSE_V dist/bdist-py$PY_VER/$N dist/$NN
      rm $VERBOSE_V -r dist/bdist-py$PY_VER
      # xxx: todo: upload
      # smisk-M.m.b[tag]-pyM.m-system-arch.tar.gz
      # smisk-1.0.1dev3-py2.5-macosx-10.3-i386.tar.gz
      
    done
    
    FILES_CREATED="$FILES_CREATED dist/*.egg"
  fi
  
  if [ $UPLOAD -eq 1 ]; then
    PKG_PREFIX=$(cd dist && echo *.tar.gz | cut -d- -f1,2 | sed 's/\.tar\.gz$//g')
  
    if [ $UPLOAD_CHECKSUMS -eq 1 ]; then
      echo "Calculating checksums"
      openssl dgst -md5 -hex $FILES_CREATED > dist/$PKG_PREFIX.md5 || exit 1
    fi
  
    if [ $UPLOAD_SIGN -eq 1 ]; then
      echo "Signing files"
      gpg_init
      for f in $FILES_CREATED; do
        v_echo "Signing $f"
        if ! gpg --detach-sign $GPG_FLAGS --armor "$f"; then
          gpg_finalize
          exit 1
        fi
        FILES_CREATED="$FILES_CREATED $f.asc"
      done
    fi
    
    # Gotta do this after signing or else we would sign the checksum file :P
    if [ $UPLOAD_CHECKSUMS -eq 1 ]; then
      FILES_CREATED="$FILES_CREATED dist/$PKG_PREFIX.md5"
    fi
    
    gpg_finalize
    
    echo "Uploading to $REMOTE_HOST:$REMOTE_PATH"
    scp -C $SCP_FLAGS $FILES_CREATED "$REMOTE_HOST:$REMOTE_PATH" || exit 1
    
    echo "Registering with PyPI"
    $DEFAULT_PYTHON setup.py $VERBOSE_SETUP_PY register || exit 1
  fi
  
fi

exit 0