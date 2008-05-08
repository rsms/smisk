#!/bin/sh
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

REMOTE_HOST='trac.hunch.se'
REMOTE_PATH='/var/lib/trac/smisk/dist/'
REMOTE_PATH_DOCS='/var/lib/trac/smisk/docs/'

if [ $# -eq 0 ] || [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
  echo "usage: $0 python-binary[, python-binary[, ...]]" >&2
  exit 1
fi

cd `dirname $0`
. dist.sh

ensure_clean_working_revision


# Clean previous built distribution packages
rm -vf dist/*.tar.gz
rm -vf dist/ready/*.tar.gz
mkdir -vp dist/ready


# Execute for each python environment
for PYTHON in $@; do
  
  # Find package name & version if not found already.
  # Also, create source distribution:
  if [ "$HAS_PERFORMED_SDIST" == "" ]; then
    $PYTHON setup.py sdist --formats=gztar
    mv -v dist/$PACKAGE-$VER.tar.gz dist/ready/
    HAS_PERFORMED_SDIST=y
  fi

  # Run distutils
  $PYTHON setup.py build --force
  $PYTHON setup.py bdist --formats=gztar

  # Add python version
  PY_VER=$(echo $($PYTHON -V 2>&1)|sed 's/[^0-9\.]//g'|cut -d . -f 1,2)
  BDIST_FILE_ORG=$(echo dist/$PACKAGE-$VER???????*.tar.gz)
  BDIST_FILE=$(echo "$BDIST_FILE_ORG"|sed 's/\.tar\.gz$/-py'$PY_VER'.tar.gz/g');
  mv -v $BDIST_FILE_ORG $BDIST_FILE
  if [ $? -ne 0 ]; then
    echo "Failed to mv $BDIST_FILE_ORG $BDIST_FILE" >&2
    exit 1
  fi
  mv -v $BDIST_FILE dist/ready/
  
done # end of each python env

# Generate documentation
$PYTHON setup.py apidocs

# Upload & update links on server
echo "Uploading dist/ready/$PACKAGE-$VER*.tar.gz to $REMOTE_HOST"
CMD="cd $REMOTE_PATH;\
for f in $PACKAGE-$VER*.tar.gz;do \
  if [ -f \"\$f\" ]; then\
    lname=\`echo \"\$f\"|sed 's/$VER/latest/g'\`;\
    ln -sf \"\$f\" \"\$lname\";\
  fi;\
done"
if is_local_host $REMOTE_HOST; then
  cp dist/ready/$PACKAGE-$VER*.tar.gz $REMOTE_PATH
  sh -c $CMD
  if [ -d doc/api ]; then
    echo "Copying doc/api"
    cp -rf doc/api $REMOTE_PATH_DOCS
  fi
else
  scp -qC dist/ready/$PACKAGE-$VER*.tar.gz $REMOTE_HOST:$REMOTE_PATH
  ssh $REMOTE_HOST $CMD
  if [ -d doc/api ]; then
    echo "Uploading doc/api to $REMOTE_HOST"
    scp -qCr doc/api $REMOTE_HOST:$REMOTE_PATH_DOCS
  fi
fi
