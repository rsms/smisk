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

# Find project revision
REV=0
for r in `svn info --recursive --non-interactive|grep 'Revision:'|awk '{print $2}'`
do
	if [ $r -gt $REV ]; then
		REV=$r
	fi
done
if [ $? != 0 ]; then
	exit $?
fi


# Update project revision in setup.py
sed -E -i .backup "s/ProjectRevision:[^\\$]+/ProjectRevision: $REV/g" setup.py
if [ $? == 0 ]; then
	rm -f setup.py.backup
else
	exit $?
fi


# Find version and update module.h
VER=`python setup.py --version`
sed -E -i .backup "s/#define PY_FCGI_VERSION \"[^\"]+\"/#define PY_FCGI_VERSION \"$VER\"/g" src/module.h
if [ $? == 0 ]; then
	rm -f src/module.h.backup
else
	exit $?
fi


# Run distutils
python setup.py build --force
python setup.py sdist
python setup.py bdist


# Fix strange OS X .3 on .4 systems for binary dist name
uname -a|grep -q 'Darwin Kernel Version 8.9'
if [ $? == 0 ]; then
	for f in dist/*macosx-10.3-*
	do
		if [ -f "$f" ]; then
			nf=`echo "$f"|sed 's/macosx-10.3/macosx-10.4/g'`
			echo mv "$f" "$nf"
			mv "$f" "$nf"
		fi
	done
fi


# Upload & update "latest"-links
echo "Uploading dist/py-fcgi-$VER*.tar.gz..."
scp -q dist/py-fcgi-$VER*.tar.gz trac.hunch.se:/var/www/rasmus/hunch.se/trac/pyfcgi/htdocs/dist/
ssh trac.hunch.se "cd /var/www/rasmus/hunch.se/trac/pyfcgi/htdocs/dist/;\
for f in py-fcgi-$VER*.tar.gz;do \
	if [ -f \"\$f\" ]; then\
		lname=\`echo \"\$f\"|sed 's/$VER/latest/g'\`;\
		ln -sf \"\$f\" \"\$lname\";\
	fi;\
done"
