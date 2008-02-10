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

cd `dirname $0`
REV=`svnversion -n`
PACKAGE=`python setup.py --name`
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
python setup.py build --force
python setup.py sdist --formats=gztar
python setup.py bdist --formats=gztar


# Upload & update "latest"-links
VER=`python setup.py --version`
echo "Uploading dist/$PACKAGE-$VER*.tar.gz..."
scp -q dist/$PACKAGE-$VER*.tar.gz $REMOTE_HOST:$REMOTE_PATH
ssh $REMOTE_HOST "cd $REMOTE_PATH;\
for f in $PACKAGE-$VER*.tar.gz;do \
	if [ -f \"\$f\" ]; then\
		lname=\`echo \"\$f\"|sed 's/$VER/latest/g'\`;\
		ln -sf \"\$f\" \"\$lname\";\
	fi;\
done"
