#!/bin/bash
#
# Build and distribute Debian packages
#
# Examples:
#
#   Build and upload both binary and source packages
#   admin/dist-debian.sh -u
#
#   Build and upload binary package
#   admin/dist-debian.sh -u -b
#
#   Build source package
#   admin/dist-debian.sh -s
#

usage() { (cat <<USAGE
Usage: $0 [-u] [options to dpkg-buildpackage]
  Build Debian packages [and upload to hunch Debian repository].
Options:
  -u  Upload the resulting packages to the hunch Debian repository using dupload.
USAGE
  ) >&2
}

# Take care of arguments
RUN_DUPLOAD=0
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
  echo "$0:" 'This is not a debian system or dpkg-buildpackage is not available.' >&2
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
  echo "$0:" "Error: Changelog out of date" >&2
  echo "$0:" "Run dch -v $UPSTREAM_VER-"$(expr $DEB_REVISION + 1)" and write a new changelog entry."
  exit 1
fi

# Make a clean copy of the repository if we're building from a checkout
CLEAN_COPY_DIR=
ORG_DIR=$(pwd)
SMISK_BUILD_ID=$(python setup.py --print-build-id)
if [ -d .git ]; then
  CLEAN_COPY_DIR=$(mktemp -d -t dist-debian.XXXXXXXXXX)
  echo "$0:" "Creating a temporary, clean clone of the repository in $CLEAN_COPY_DIR"
  trap "rm -rf $CLEAN_COPY_DIR; exit $?" INT TERM EXIT
  CLEAN_COPY_DIR=${CLEAN_COPY_DIR}/${DEB_PACKAGE_NAME}-${UPSTREAM_VER}
  git clone --local --quiet "${ORG_DIR}" ${CLEAN_COPY_DIR}
  cd ${CLEAN_COPY_DIR}
  rm -rf .git*
fi
export SMISK_BUILD_ID="${SMISK_BUILD_ID}:debian:${DEB_REVISION}"

# Test working copy
for PV in  2.4  2.5  2.6  2.7 ; do
  if (which python$PV>/dev/null); then
    echo "$0:" "Building and testing working copy Smisk with Python $PV"
    python$PV setup.py build -f > /dev/null
    PYTHONPATH=$(echo $(pwd)/build/lib.*-$PV) python$PV -c 'import smisk.test as t;t.test()' > /dev/null || exit 1
  fi
done

# Build
echo "$0:" "Running dpkg-buildpackage -rfakeroot ${args}"
dpkg-buildpackage -rfakeroot ${args} || exit 1

# Move files to a better location
rm -rf "${ORG_DIR}/dist/debian" || exit 1
mkdir -vp "${ORG_DIR}/dist/debian" || exit 1
mv -v ../${DEB_PACKAGE_NAME}_${UPSTREAM_VER}-${DEB_REVISION}* "${ORG_DIR}/dist/debian/" || exit 1

# Upload
if [ $RUN_DUPLOAD -eq 1 ]; then
  echo "$0:" "Running dupload -t hunch dist/debian"
  dupload -t hunch "${ORG_DIR}/dist/debian"
else
  echo "$0:" "Upload disabled -- to manually upload the build package(s), run:"
  echo "dupload -t hunch '${ORG_DIR}/dist/debian'"
fi
