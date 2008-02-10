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

cd `dirname $0`
if [ "$1" != "" ]; then PYTHON="$1"; else PYTHON=$(which python); fi
REV=`svnversion -n`
PACKAGE=`$PYTHON setup.py --name`
REMOTE_HOST='trac.hunch.se'
REMOTE_PATH='/var/lib/trac/smisk/dist/'
DEB_REMOTE_HOST='hunch.se'
DEB_REMOTE_PATH='/var/www/hunch.se/www/public/debian/'
GREP=`which grep`

# Confirm working revision is synchronized with repository
if [ $(echo "$REV"|$GREP -E '[:SM]') ]; then
  echo "Working revision $REV is not up-to-date. Commit and/or update first."
  exit 1
fi

# Clean previous built distribution packages
rm -vf dist/*.tar.gz

# Run distutils
$PYTHON setup.py build --force
$PYTHON setup.py sdist --formats=gztar
$PYTHON setup.py bdist --formats=gztar

# Add python version
PY_VER=$(echo $($PYTHON -V 2>&1)|sed 's/[^0-9\.]//g'|cut -d . -f 1,2)
BDIST_FILE_ORG=$(echo dist/$PACKAGE-$VER???????*.tar.gz)
BDIST_FILE=$(echo "$BDIST_FILE_ORG"|sed 's/\.tar\.gz$/-py'$PY_VER'.tar.gz/g');
mv $BDIST_FILE_ORG $BDIST_FILE
if [ $? -ne 0 ]; then
  echo "Failed to mv $BDIST_FILE_ORG $BDIST_FILE" >&2
  exit 1
fi

# Upload & update "latest"-links
VER=`$PYTHON setup.py --version`
echo "Uploading dist/$PACKAGE-$VER*.tar.gz..."
scp -q dist/$PACKAGE-$VER*.tar.gz $REMOTE_HOST:$REMOTE_PATH
ssh $REMOTE_HOST "cd $REMOTE_PATH;\
for f in $PACKAGE-$VER*.tar.gz;do \
	if [ -f \"\$f\" ]; then\
		lname=\`echo \"\$f\"|sed 's/$VER/latest/g'\`;\
		ln -sf \"\$f\" \"\$lname\";\
	fi;\
done"

# If we're on Debian, do the Debian-disco:
if [ -f /etc/apt/sources.list ]; then
  dpkg-buildpackage -rfakeroot
  scp -q ../python-${PACKAGE}_${VER}-*.* $DEB_REMOTE_HOST:$DEB_REMOTE_PATH
fi
