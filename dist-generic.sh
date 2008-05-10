#!/usr/bin/env bash
#
# Perform a complete distribution.
#
#  - Update setup.py and src/module.h with current version (including revision)
#  - (Re)Build everything
#  - Create source distribution
#  - Create binary distribution
#  - Upload packages and update remote "latest"-links
#
# Arguments
#   1:  Path to python binary for which environment to build and
#       distribute for.
#

# Paths defined here must be absolute
REMOTE_HOST='trac.hunch.se'
REMOTE_PATH='/var/lib/trac/smisk/dist/'
REMOTE_PATH_DOCS='/var/lib/trac/smisk/docs/'

usage() { (cat <<USAGE
Usage: $0 [options] [python ...]
Options:
 -h   Display help and exit.
 -m   Milestone release. Do not include "dev-SERIAL-REV" in package filenames.
 -u   Distribute/upload the resulting packages.
      specified and generated documentation exists in doc/api.
 -b   Do NOT build binary package(s).
 -d   Do NOT generate documentation.
 -p   Do NOT upload documentation. Only effective if -d is specified, -n is not
 -s   Do NOT build source package.
USAGE
  ) >&2
}

# Default options
DISTRIBUTE=0
IS_MILESTONE=0
GENERATE_BINARY=1
GENERATE_SOURCE=1
GENERATE_DOCS=1

# Parse options
while getopts 'dhmn' OPTION; do
  case $OPTION in
    d)  DISTRIBUTE=1 ;;
    m)  IS_MILESTONE=1 ;;
    n)  GENERATE_DOCS=0 ;;
    h)  echo "Smisk distribution script" >&2 ; usage ; exit 2 ;;
    *)  usage ; exit 2 ;;
  esac
done
shift $(($OPTIND - 1))
if [ $GENERATE_BINARY -eq 1 ] && [ $# -eq 0 ]; then
  echo "$0: no python interpreters specified" >&2
  usage ; exit 3
fi


# Include shared stuff
cd `dirname $0`
. dist.sh || exit 1


ensure_clean_working_revision


# Construct dev extension for filenames
if [ $IS_MILESTONE -eq 0 ]; then
  DEVEXT="-dev-$(date '+%y%m%d%H%M')-$REV"
else
  # Info about milestone production
  if [ $DISTRIBUTE -eq 1 ] && [ $GENERATE_BINARY -eq 1 ]; then
    echo "Producing and distributing Milestone"
  elif [ $DISTRIBUTE -eq 1 ]; then
    echo "Distributing (but not producing) Milestone"
  elif [ $GENERATE_BINARY -eq 1 ]; then
    echo "Producing (but not distributing) Milestone"
  else
    echo "Warning: -m (Milestone) is set but neither production nor distribution is enabled." >&2
    read -n 1 -p 'Continue anyway? [y/N] ' ANSWER
    if [ "$ANSWER" != "y" ] && [ "$ANSWER" != "Y" ]; then
      exit 1
    fi
  fi
fi


# Clean dist directories
if [ $GENERATE_BINARY -eq 1 ] || [ $GENERATE_SOURCE -eq 1 ]; then
  echo '------------------------'
  echo 'Cleaning dist dir...'
  rm -vf dist/*.*
  rm -vf dist/ready/*.*
  mkdir -vp dist/ready
fi


# Build binary packages
if [ $GENERATE_BINARY -eq 1 ]; then
  for PYTHON in $@; do
    # Simple sanity check
    echo '------------------------'
    echo -n 'Building with '
    ($PYTHON -V) || exit 1
  
    # Run distutils
    $PYTHON setup.py build --force || exit 1
    $PYTHON setup.py bdist --formats=gztar || exit 1

    # Rename resulting file
    PY_VER=$(echo $($PYTHON -V 2>&1) | sed 's/[^0-9\.]//g' | cut -d . -f 1,2)
    BDIST_FILE_ORG="$(basename "$(echo dist/$PACKAGE-$VER*.tar.gz)")"
    # Convert smisk-1.0.0.system --> smisk-1.0.0-system and Add python version
    BDIST_FILE="$(echo "$BDIST_FILE_ORG" | sed 's/-'$VER'./-'$VER'-/' | sed 's/\.tar\.gz$/-py'$PY_VER'.tar.gz/')"
    if [ $IS_MILESTONE -eq 0 ]; then
      # Append <"dev-" dateserial "-" revision> to version
      BDIST_FILE="$(echo "$BDIST_FILE" | sed 's/-'$VER'/-'${VER}${DEVEXT}'/')"
    fi
    mv -v "dist/$BDIST_FILE_ORG" "dist/ready/$BDIST_FILE" || exit 1
  done # end of each python env
fi


# Create source distribution
if [ $GENERATE_SOURCE -eq 1 ]; then
  echo '------------------------'
  echo 'Generating source package'
  $DEFAULT_PYTHON setup.py --quiet sdist --formats=gztar || exit 1
  if [ $IS_MILESTONE -eq 0 ]; then
    mv -v "dist/$PACKAGE-$VER.tar.gz" "dist/ready/$PACKAGE-${VER}${DEVEXT}.tar.gz"
  else
    mv -v "dist/$PACKAGE-$VER.tar.gz" "dist/ready/"
  fi
fi


# Generate documentation
if [ $GENERATE_DOCS -eq 1 ]; then
  echo '------------------------'
  echo 'Generating documentation'
  $DEFAULT_PYTHON setup.py apidocs
fi


# Distribute
if [ $DISTRIBUTE -eq 1 ]; then
  if [ $GENERATE_DOCS -eq 1 ] && [ ! -f doc/api/index.html ]; then
    echo 'Warning: Will not be distributed -- doc/api does not exist but was intended to be created.' >&2
    GENERATE_DOCS=0
  fi
  
  FNPATTERN="${DEB_PACKAGE_NAME}_${CURRENT_VER}-${DEB_PACKAGE_VER}"
  echo '------------------------'
  echo -n "Copying dist/ready/$PACKAGE-$VER*.tar.gz to "
  
  CMD="cd $REMOTE_PATH;\
  for f in $PACKAGE-$DIST_ID*.tar.gz;do \
    if [ -f \"\$f\" ]; then\
      lname=\`echo \"\$f\"|sed 's/$DIST_ID/latest/g'\`;\
      ln -sf \"\$f\" \"\$lname\";\
    fi;\
  done"
  if is_local_host $REMOTE_HOST; then
    echo $REMOTE_PATH
    cp dist/ready/$PACKAGE-$VER*.tar.gz $REMOTE_PATH
    echo $CMD | sh --verbose || exit 1
    if [ $GENERATE_DOCS -eq 1 ]; then
      echo "Copying doc/api to $REMOTE_PATH_DOCS/api"
      cp -rf doc/api $REMOTE_PATH_DOCS/api-new
      mv -vf $REMOTE_PATH_DOCS/api-new $REMOTE_PATH_DOCS/api
    fi
  else
    echo "$REMOTE_HOST:$REMOTE_PATH"
    scp -qC dist/ready/$PACKAGE-$VER*.tar.gz $REMOTE_HOST:$REMOTE_PATH || exit 1
    ssh $REMOTE_HOST $CMD || exit 1
    if [ $GENERATE_DOCS -eq 1 ]; then
      echo "Copying doc/api to $REMOTE_HOST:$REMOTE_PATH_DOCS/api"
      scp -qCr doc/api $REMOTE_HOST:$REMOTE_PATH_DOCS/api-new
      ssh $REMOTE_HOST "mv -vf $REMOTE_PATH_DOCS/api-new $REMOTE_PATH_DOCS/api"
    fi
  fi
fi

echo 'Done'
exit 0
