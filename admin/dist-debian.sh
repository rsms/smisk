#!/bin/bash
#
# Build and distribute Debian packages
#
RUN_DUPLOAD=0
DEB_BRANCH='unstable'
DEB_REMOTE_HOST='rasmus@hunch.se'
DEB_REMOTE_PATH='/var/www/hunch.se/www/public/debian/'

# ----------------------------------

usage() { (cat <<USAGE
Usage: $0 [-u] [options to dpkg-buildpackage]
  Build Debian packages [and upload to hunch Debian repository].
Options:
  -u  Upload the resulting packages to the hunch Debian repository using dupload.
USAGE
  ) >&2
}

# Take care of arguments
args=( $* )
if [ $# -gt 0 ]; then
  if [ "$1" = "-u" ]; then
    RUN_DUPLOAD=1
    args=${args[@]:1}
  elif [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
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
UPSTREAM_VER=$VER
PREV_UPSTREAM_VER=$(head -n 1 debian/changelog | cut -d ' ' -f 2 | cut -d - -f 1 | sed 's/(//')
DEB_PACKAGE_NAME="python-$PACKAGE"
DEB_REVISION=$(head -n 1 debian/changelog | cut -d ' ' -f 2 | cut -d - -f 2 | sed 's/)//')
DEB_BRANCH=$(head -n 1 debian/changelog | cut -d ' ' -f 3 | sed 's/;//')

ensure_clean_working_revision

if [ "$PREV_UPSTREAM_VER" != "$UPSTREAM_VER" ]; then
  echo "Error: Changelog out of date" >&2
  echo "Run dch -v $UPSTREAM_VER-"$(expr $DEB_REVISION + 1)" and write a new changelog entry."
  exit 1
fi

# Make a clean copy of the repository if we're building from a checkout
CLEAN_COPY_DIR=
ORG_DIR=$(pwd)
if [ -d .hg ]; then
  echo 'Creating a temporary, clean clone of this repository'
  CLEAN_COPY_DIR=$(mktemp -d -t dist-debian.XXXXXXXXXX)
  trap "rm -rf $CLEAN_COPY_DIR; exit $?" INT TERM EXIT
  CLEAN_COPY_DIR=${CLEAN_COPY_DIR}/${DEB_PACKAGE_NAME}-${UPSTREAM_VER}
  hg clone "${ORG_DIR}" ${CLEAN_COPY_DIR}
  cd ${CLEAN_COPY_DIR}
  rm -rf .hg*
fi

# Build
echo 'Running dpkg-buildpackage -rfakeroot'
dpkg-buildpackage -rfakeroot ${args} || exit 1

# Move files to a better location
rm -rf "${ORG_DIR}/dist/debian" || exit 1
mkdir -vp "${ORG_DIR}/dist/debian" || exit 1
mv -v ../${DEB_PACKAGE_NAME}_${UPSTREAM_VER}-${DEB_REVISION}* "${ORG_DIR}/dist/debian/" || exit 1

# Upload
if [ $RUN_DUPLOAD -eq 1 ]; then
  echo "Running dupload -t hunch.se-${DEB_BRANCH} dist/debian"
  dupload -t hunch.se-${DEB_BRANCH} "${ORG_DIR}dist/debian"
else
  echo "Upload disabled -- to manually upload the build package(s), run:"
  echo "dupload -t hunch.se-${DEB_BRANCH} '${ORG_DIR}/dist/debian'"
fi
