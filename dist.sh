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
VERV=$(echo "$VER"|cut -d - -f 1)
REV=$(echo "$VER"|cut -d - -f 2)


# Confirm working revision is synchronized with repository
ensure_clean_working_revision() {
  RREV=$REV
  if (echo "$RREV"|$GREP '+' > /dev/null); then
    echo "Working revision $RREV is not up-to-date. You need to sort things out first."
    exit 1
  fi
}


is_local_host() {
  if [ "$(host -Qt A $1|cut -f 3)" == "$(host -Qt A $(hostname --fqdn)|cut -f 3)" ]; then
    return 0
  fi
  return 1
}

