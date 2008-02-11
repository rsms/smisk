#!/bin/sh

# Remote repository in which to put final packages
DEB_REMOTE_HOST='hunch.se'
DEB_REMOTE_PATH='/var/www/hunch.se/www/public/debian/'

# ----------------------------------
cd `dirname $0`
. dist.sh

# Ensure we're on Debian and has package builder
if [ $(uname -s) != "Linux" ] || [ ! -x /usr/bin/dpkg-buildpackage ]; then
  echo 'This is not a debian machine or dpkg-buildpackage is not available.' >&2
  exit 1
fi

ensure_clean_working_revision


# Ensure debian/changelog is updated
for r in $(grep -E '\([0-9\.]+r[0-9]+-[0-9]+\)' debian/changelog|cut -d ' ' -f 2|sed -r 's/\([0-9\.]+r([0-9]+-[0-9]+)\)/\1/g'); do
  if [ "$PREV_DEB_REV" == "" ]; then
    PREV_DEB_REV=$(echo $r|cut -d - -f 1)
    PREV_DEB_DEBV=$(echo $r|cut -d - -f 2)
  fi
done
if [ $PREV_DEB_REV -lt $(expr $REV - 1) ]; then
  LESS=$(which less)
  if [ "$LESS" == "" ]; then LESS=$(which more); fi
  if [ "$LESS" == "" ]; then LESS=$(which cat); fi
  CHANGELOG_URL="http://trac.hunch.se/${PACKAGE}/log?rev=${REV}&stop_rev=$(expr $PREV_DEB_REV - 1)&limit=500&mode=follow_copy"
  echo 'The debian/changelog need to be updated.'
  echo '-------------------------------'
  echo 'You can view a more detailed revision changelog here:'
  echo $CHANGELOG_URL'&verbose=on'
  echo '-------------------------------'
  NEED_ANSWER=1
  while [ $NEED_ANSWER -eq 1 ]; do
    echo "[1] Review changes between r${REV} and r$(expr $PREV_DEB_REV - 1), then return here."
    echo '[2] Help me edit debian/changelog and continue.'
    echo -n 'Enter your choice [1-2]: (2) '
    read ANSWER
    if [ "$ANSWER" == "" ]; then ANSWER=2; fi
    case $ANSWER in
      1) curl --silent "${CHANGELOG_URL}&format=changelog"|$LESS ;;
      2) NEED_ANSWER=0 ;;
      *) ;;
    esac
  done
  # Create a changelog message
  for r in $(grep -E '^ -- ' debian/changelog|sed -r 's/ -- (.+<[^>]+>).+/\1/g'|sed 's/ /___/g'); do
    if [ "$PREV_DEB_CONTACT" == "" ]; then
      PREV_DEB_CONTACT=$(echo "$r"|sed 's/___/ /g');
    fi
  done
  echo "python-$PACKAGE ($VER-$(expr $PREV_DEB_DEBV + 1)) unstable; urgency=low" > debian/changelog.tmp
  echo >> debian/changelog.tmp
  echo '  * '>> debian/changelog.tmp
  echo >> debian/changelog.tmp
  echo " -- $PREV_DEB_CONTACT $(date --rfc-2822)">> debian/changelog.tmp
  echo >> debian/changelog.tmp
  cat debian/changelog >> debian/changelog.tmp
  NEED_ANSWER=1
  while [ $NEED_ANSWER -eq 1 ]; do
    SUM_BEFORE=$(md5sum debian/changelog.tmp|cut -d ' ' -f 1)
    $EDITOR debian/changelog.tmp
    SUM_AFTER=$(md5sum debian/changelog.tmp|cut -d ' ' -f 1)
    if [ "$SUM_AFTER" == "$SUM_BEFORE" ]; then
      echo 'The debian/changelog message unchanged or not specified.'
      echo -n 'a)bort, c)ontinue, e)dit: (e) '
      read ANSWER
      case $ANSWER in
        a) rm debian/changelog.tmp ; exit 2 ;;
        c) NEED_ANSWER=0 ;;
        *) ;;
      esac
    else
      NEED_ANSWER=0
    fi
  done
  mv debian/changelog.tmp debian/changelog
  echo 'debian/changelog updated.'
  if [ -d .svn ]; then
    echo 'Committing changelog update to subversion'
    svn ci -m 'Debian changelog message added' debian/changelog
    svn up
  fi
  ensure_clean_working_revision
fi


# Build
if ! dpkg-buildpackage -rfakeroot; then
  exit $?
fi


# Upload/Move
if is_local_host $DEB_REMOTE_HOST; then
  echo "Moving ../python-${PACKAGE}_${VER}-*.* to $DEB_REMOTE_PATH"
  mv -vf ../python-${PACKAGE}_${VER}-*.* $DEB_REMOTE_PATH
else
  echo "Uploading ../python-${PACKAGE}_${VER}-*.* to $DEB_REMOTE_HOST"
  scp -qC ../python-${PACKAGE}_${VER}-*.* $DEB_REMOTE_HOST:$DEB_REMOTE_PATH
fi
