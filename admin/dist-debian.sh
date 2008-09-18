#!/bin/sh
#
# Build and distribute Debian packages
#

DEB_BRANCH='unstable'
DISTRIBUTE=0
DEB_REMOTE_HOST='rasmus@hunch.se'
DEB_REMOTE_PATH='/var/www/hunch.se/www/public/debian/'

# ----------------------------------

usage() { (cat <<USAGE
Usage: $0 [-u]
  Build Debian packages [and upload to hunch Debian repository].
Options:
  -u  Upload the resulting packages to the hunch Debian repository.
USAGE
  ) >&2
}

# Take care of arguments
if [ $# -gt 0 ]; then
  if [ "$1" = "-u" ]; then
    DISTRIBUTE=1
  else
    usage ; exit 1
  fi
fi


# Ensure we're on Debian and has package builder
if [ $(uname -s) != "Linux" ] || [ ! -x /usr/bin/dpkg-buildpackage ]; then
  echo 'This is not a debian system or dpkg-buildpackage is not available.' >&2
  exit 1
fi


# Properties
cd "$(dirname "$0")/.."
. admin/dist-base.sh || exit 1

DEB_PACKAGE_NAME="python-$PACKAGE"
CURRENT_VER=$VER  # just gives this a better name
PREV_VER=         # 1.0.1
PREV_PKGVER=      # 7
DEB_PACKAGE_VER=  # 1


# Get info about the latest version from the changelog
for r in $(grep -E "${DEB_PACKAGE_NAME} "'\(.+-[0-9]+\)' debian/changelog | cut -d ' ' -f 2 | sed -r 's/(\(|\))//g'); do
  if [ -z $PREV_VER ]; then
    PREV_VER=$(echo $r|cut -d - -f 1)
    PREV_PKGVER=$(echo $r|cut -d - -f 2)
  fi
done


ensure_clean_working_revision


if [ "$PREV_VER" = "$CURRENT_VER" ]; then
  echo 'The program version AND package version seems to be up to date in '
  echo 'the changelog. Make sure you have updated it. (For example the '
  echo "debian package version which is now ${PREV_PKGVER})"
  read -n 1 -p 'Build package with current changelog? [Y/n] ' ANSWER
  if [ "$ANSWER" != "" ] && [ "$ANSWER" != "y" ] && [ "$ANSWER" != "Y" ]; then
    echo
    echo 'Aborted by user' >&2
    exit 1
  fi
  DEB_PACKAGE_VER=$PREV_PKGVER
  # continue with unmodified changelog
else
  # changelog probably out of date - ensure it's updated
  SKIP_CHANGELOG=0
  LESS=$(which less)
  if [ "$LESS" = "" ]; then LESS=$(which more); fi
  if [ "$LESS" = "" ]; then LESS=$(which cat); fi

  echo 'The debian/changelog needs to be updated.
-------------------------------
You can view a more detailed revision changelog here:
http://trac.hunch.se/${PACKAGE?}/log
Note: Editing the changelog through this interface will case a RSC commit.
-------------------------------'
  NEED_ANSWER=1
  while [ $NEED_ANSWER -eq 1 ]; do
    echo '[1] Help me edit debian/changelog and continue.
[2] Contiune without modifying the changelog. (Not recommended)
CTRL+C to abort.'
    read -n 1 -p 'Enter your choice [1-2]: (1) ' ANSWER
    if [ "$ANSWER" = "" ]; then ANSWER=1; fi
    case $ANSWER in
      1) NEED_ANSWER=0 ;;
      2) NEED_ANSWER=0; SKIP_CHANGELOG=1 ;;
      *) ;;
    esac
  done

  if [ $SKIP_CHANGELOG -eq 0 ]; then
    
    # Make sure the version is changed
    if [ "$PREV_VER" != "$CURRENT_VER" ]; then
      DEB_PACKAGE_VER=1
      echo "Package version reset to 1 due to new program version"
    else
      DEB_PACKAGE_VER=$(expr $DEB_PACKAGE_VER + 1)
      echo "Package version bumped up to $DEB_PACKAGE_VER due to unchanged program version"
    fi
    
    # Construct a changelog message
    for r in $(grep -E '^ -- ' debian/changelog|sed -r 's/ -- (.+<[^>]+>).+/\1/g'|sed 's/ /___/g'); do
      if [ "$PREV_DEB_CONTACT" = "" ]; then
        PREV_DEB_CONTACT=$(echo "$r"|sed 's/___/ /g');
      fi
    done
    echo "${DEB_PACKAGE_NAME} (${CURRENT_VER}-${DEB_PACKAGE_VER}) ${DEB_BRANCH}; urgency=low" > debian/changelog.tmp
    echo >> debian/changelog.tmp
    echo '  * '>> debian/changelog.tmp
    echo >> debian/changelog.tmp
    echo " -- $PREV_DEB_CONTACT  $(date --rfc-2822)">> debian/changelog.tmp
    echo >> debian/changelog.tmp
    cat debian/changelog >> debian/changelog.tmp || exit 1
    
    
    # Let the user modify and update the changelog
    NEED_ANSWER=1
    while [ $NEED_ANSWER -eq 1 ]; do
      SUM_BEFORE=$(md5sum debian/changelog.tmp|cut -d ' ' -f 1)
      $EDITOR debian/changelog.tmp
      SUM_AFTER=$(md5sum debian/changelog.tmp|cut -d ' ' -f 1)
      if [ "$SUM_AFTER" = "$SUM_BEFORE" ]; then
        echo 'The debian/changelog message unchanged or not specified.'
        read -n 1 -p 'a)bort, c)ontinue, e)dit: (e) ' ANSWER
        case $ANSWER in
          a) rm debian/changelog.tmp ; exit 2 ;;
          c) NEED_ANSWER=0 ;;
          *) ;;
        esac
      else
        NEED_ANSWER=0
      fi
    done
    mv debian/changelog.tmp debian/changelog || exit 1
    echo 'debian/changelog updated'
    
    
    # Commit changes to the changelog
    if [ -d .svn ]; then
      echo 'Committing changelog update'
      svn ci -m 'Debian changelog updated (dist-debian.sh)' debian/changelog
      svn up
    elif [ -d .hg ]; then
      echo 'Committing changelog update'
      hg ci -m 'Debian changelog updated (dist-debian.sh)' debian/changelog
    fi
    ensure_clean_working_revision
    
  fi # [ $SKIP_CHANGELOG -eq 0 ]
  
fi # [ "$PREV_VER" = "$CURRENT_VER" ] && [ "$PREV_PKGVER" = "$DEB_PACKAGE_VER" ] else

# Build
echo 'Running dpkg-buildpackage -rfakeroot'
dpkg-buildpackage -rfakeroot -us -uc || exit 1


# Move files to a better location
# XXX: This should dpkg-buildpackage be able to do. Checked it up quickly but did not find anything.
FNPATTERN="${DEB_PACKAGE_NAME}_${CURRENT_VER}-${DEB_PACKAGE_VER}"
rm -rf dist/debian || exit 1
mkdir -vp dist/debian || exit 1
mv -v ../$FNPATTERN* dist/debian/ || exit 1


# Distribute
if [ $DISTRIBUTE -eq 1 ]; then
  echo "Running dupload -t hunch.se dist/debian"
  dupload -t hunch.se dist/debian
fi
