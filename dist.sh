#!/bin/sh

if [ "$(echo $0|grep -E 'dist.sh$')" != "" ]; then
  echo "You should not run this file directly, but one of these:" >&2
  echo $(/bin/ls dist-*.sh) >&2
  exit 1
fi

GREP=$(which grep)
DEFAULT_PYTHON=$(which python)
PACKAGE=$($DEFAULT_PYTHON setup.py --name)
VER=$($DEFAULT_PYTHON setup.py --version)
REV=$(echo "$VER"|sed -r 's/.+r(.+)/\1/g')
if [ -d .svn ]; then SVN=1; fi


# Confirm working revision is synchronized with repository
ensure_clean_working_revision() {
  if [ "$(echo "$REV"|$GREP -E '[:SM]')" != "" ]; then
    echo "Working revision $REV is not up-to-date. Commit and/or update first."
    exit 1
  fi
}


is_local_host() {
  if [ "$(host -Qt A $1|cut -f 3)" == "$(host -Qt A $(hostname -a)|cut -f 3)" ]; then
    return 0
  fi
  return 1
}

