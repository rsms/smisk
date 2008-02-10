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


if [ $(echo "$REV"|grep ':') ]; then
  echo "Working revision $REV is mixed. Commit and/or update first."
  exit 1
elif [ $(echo "$REV"|grep 'M') ]; then
  echo "Working revision $REV is modified. Commit and/or update first."
  exit 1
elif [ $(echo "$REV"|grep 'S') ]; then
  echo "Working revision $REV is switched. Commit and/or update first."
  exit 1
fi


# Run distutils
$PYTHON setup.py build --force
$PYTHON setup.py sdist --formats=gztar
$PYTHON setup.py bdist --formats=gztar


# Add python version
PY_VER=$(echo $($PYTHON -V 2>&1)|sed 's/[^0-9\.]//g'|cut -d . -f 1,2)
BDIST_FILE_ORG=$(echo dist/$PACKAGE-$VER???????*.tar.gz)
BDIST_FILE=$(echo "$BDIST_FILE_ORG"|sed 's/\.tar\.gz$/-py'$PY_VER'.tar.gz/g');
mv $BDIST_FILE_ORG $BDIST_FILE


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
