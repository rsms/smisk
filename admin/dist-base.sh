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
REV=
if [ -d .git ]; then
  REV=$(git rev-parse master)
fi

# Security measure to make sure we don't end up with version-version
if (echo "$VER" | grep '-' >/dev/null); then
  VER=$(echo "$VER" | cut -d'-' -f 1 )
fi

# Confirm working revision is synchronized with repository
ensure_clean_working_revision() {
  RREV=$REV
  ST="$(git status 2> /dev/null | tail -n1)"
  if [[ "$ST" != "nothing to commit (working directory clean)" ]] \
  && [[ "$ST" != 'nothing added to commit but untracked files present (use "git add" to track)' ]]; then
    echo "$0: Warning: Work tree $RREV is not clean. You should commit or revert modifications." >&2
  fi
}


is_local_host() {
  if [ ! -x "$(which host)" ]; then
    return 1
  fi
  if (uname|grep 'Darwin' > /dev/null); then
    hostname=$(hostname)
  else
    hostname=$(hostname --fqdn)
  fi
  if [ "$(host -t A $1|cut -f 3)" = "$(host -t A $hostname|cut -f 3)" ]; then
    if [ $? -ne 0 ]; then
      echo "$0: Error: Failed to look up host $hostname"
      exit 1
    fi
    return 0
  fi
  return 1
}

