#!/usr/bin/env bash
#
# Perform a complete distribution.
#
# Note: This is a distribution script, not a build script. If building or
#       generating documentation is your goal, use setup.py instead.
#       Run  python setup.py --help  for more information.
#
# Note: Distribution requires access to distribution channels and will
#       fail hard if you are not authorized.
#
# Note: For Debian, see dist-debian.sh
#

# Paths defined here must be absolute and end with a slash
REMOTE_HOST='trac.hunch.se'
REMOTE_PATH='/var/lib/trac/smisk/dist/'
REMOTE_PATH_DOCS='/var/lib/trac/smisk/docs/'

usage() {
  if [ "$1" != "" ]; then
    # extended help
    echo "Smisk distribution script" >&2
    echo "" >&2
  fi
  
  # Always print this
  (cat <<USAGE
Usage: $0 [options] python ...
       $0 -b [options]
USAGE
  ) >&2
  
  if [ "$1" != "" ]; then
    # extended help
    (cat <<USAGE

Options:
 Milestone options:
  -m   Milestone release. Implies -u, -d and -c.
  -n   Do NOT generate documentation. Effective in combination with -m.
  -o   Do NOT distribute documentation. Effective in combination with -m.
 
 Snapshot options:
  -u   Distribute/upload the resulting packages excluding documentation.
  -d   Generate documentation.
  -c   Distribute documentation. Effective in combination with -d.
 
 Global options:
  -b   Do NOT build binary package(s).
  -s   Do NOT build source package.
  -l   Do NOT link as latest on distribution side.
  -r   Dry run. Show what would happen without actually doing anything.
  -p   Print configuration and exit.
  -h   Display detailed help and exit.

Milestone exaples:
  $0 -m python2.{4,5}
    Builds binary and source packages, generates documentation and pushes
    everything to appropriate distribution channels.

  $0 -mn python2.{4,5}
    Builds binary and source packages, but does NOT generate or distribute
    documentation. Pushes everything to appropriate distribution channels.

  $0 -mbs
    Generates and distributes milestone documentation.

Snapshot examples:
  $0 -u python2.{4,5}
    Builds binary and source packages and pushes everything to appropriate
    distribution channels.

  $0 python2.{4,5}
    Builds binary and source packages but does NOT distribute anything.

  $0 -ub
    Creates and distributes a snapshot source package.

  $0 -ur python2.{4,5}
    Simulates the first Snapshot example, but does not actually do anything.

USAGE
    ) >&2
  else
    echo "Run $0 -h for more details." >&2
  fi
}

# Default options
IS_MILESTONE=0
DRY_RUN=0
PRINT_CONF_AND_EXIT=0
GENERATE_BINARY=1
GENERATE_SOURCE=1
GENERATE_DOCS=
DISTRIBUTE_PKGS=
DISTRIBUTE_DOCS=
# the link is to be considered as "latest snapshot" so default on for both milestone and snapshot:
DISTRIBUTE_LINK_LATEST=1

# Parse options
while getopts 'mnoudcbslrph' OPTION; do
  case $OPTION in
    # Milestone options
    m)  IS_MILESTONE=1 ;;
    n)  GENERATE_DOCS=0 ;;
    o)  DISTRIBUTE_DOCS=0 ;;
    # Snapshot options
    u)  DISTRIBUTE_PKGS=1 ;;
    d)  GENERATE_DOCS=1 ;;
    c)  DISTRIBUTE_DOCS=1 ;;
    # Global options
    b)  GENERATE_BINARY=0 ;;
    s)  GENERATE_SOURCE=0 ;;
    r)  DRY_RUN=1 ;;
    p)  PRINT_CONF_AND_EXIT=1 ;;
    l)  DISTRIBUTE_LINK_LATEST=0 ;;
    h)  usage y ; exit 2 ;;
    *)  usage ; exit 2 ;;
  esac
done
shift $(($OPTIND - 1))

# Adjust options
if [ $IS_MILESTONE -eq 1 ]; then
  if [ -z $DISTRIBUTE_PKGS ]; then DISTRIBUTE_PKGS=1; fi
  if [ -z $GENERATE_DOCS ];   then GENERATE_DOCS=1; fi
  if [ -z $DISTRIBUTE_DOCS ]; then
    if [ $GENERATE_DOCS -eq 0 ]; then
      DISTRIBUTE_DOCS=0
    else
      DISTRIBUTE_DOCS=1
    fi
  fi
else
  if [ -z $DISTRIBUTE_PKGS ]; then DISTRIBUTE_PKGS=0; fi
  if [ -z $GENERATE_DOCS ];   then GENERATE_DOCS=0; fi
  if [ -z $DISTRIBUTE_DOCS ]; then DISTRIBUTE_DOCS=0; fi
fi

# Some options need explicit python binaries
if [ $GENERATE_BINARY -eq 1 ] && [ $# -eq 0 ]; then
  echo "$0: Error: no python interpreters specified" >&2
  usage ; exit 3
fi


# Include shared stuff
cd `dirname $0`
. dist.sh || exit 1


# Package id and version
#
# PKG_VER examples:
#   Milestone: 1.0.0
#   Snapshot:  1.0.0-dev-0805102152-d8a6d11b6cdb
#
# PKG_ID examples:
#   Milestone: smisk-1.0.0
#   Snapshot:  smisk-1.0.0-dev-0805102152-d8a6d11b6cdb
#
PKG_VER="${VER}${DEVEXT}"
if [ $IS_MILESTONE -eq 0 ]; then
  PKG_VER="${PKG_VER}-dev-$(date '+%y%m%d%H%M')-$REV"
fi
PKG_ID="${PACKAGE}-${PKG_VER}"
PKG_DISTUTILS_ID="${PACKAGE}-${VER}"


# Print configuration
echo "Configuration:"
echo -n "  Type:       "
if [ $IS_MILESTONE -eq 1 ]; then echo "Milestone"; else echo "Snapshot"; fi
if [ $GENERATE_SOURCE -eq 1 ] || [ $GENERATE_BINARY -eq 1 ]; then
  echo -n "  Identifier: $PKG_ID"
  if ([ $DRY_RUN -eq 1 ] || [ $PRINT_CONF_AND_EXIT -eq 1 ]) && [ $IS_MILESTONE -eq 0 ]; then
    echo "  (may change)"
  else
    echo
  fi
fi
echo "  Generating:"
if [ $GENERATE_BINARY -eq 1 ]; then echo "    + Binaries for $@"; fi
if [ $GENERATE_SOURCE -eq 1 ]; then echo "    + Source"; fi
if [ $GENERATE_DOCS -eq 1 ];   then echo "    + Documentation"; fi
if [ $DISTRIBUTE_PKGS -eq 1 ] || [ $DISTRIBUTE_DOCS -eq 1 ]; then
  echo "  Distributing:"
  if [ $DISTRIBUTE_PKGS -eq 1 ]; then
    if [ $GENERATE_BINARY -eq 1 ]; then echo "    + Binaries"; fi
    if [ $GENERATE_SOURCE -eq 1 ]; then echo "    + Source"; fi
  fi
  if [ $DISTRIBUTE_DOCS -eq 1 ]; then echo "    + Documentation"; fi
fi

# Disable dist if neither bin nor src is to be produced
if [ $IS_MILESTONE -eq 1 ] && [ $GENERATE_BINARY -eq 0 ] && [ $GENERATE_SOURCE -eq 0 ]; then
  DISTRIBUTE_PKGS=0
fi

# Only print configuration? If so, exit cleanly here
if [ $PRINT_CONF_AND_EXIT -eq 1 ]; then exit 0; fi

# Dry run setup
if [ $DRY_RUN -eq 1 ]; then
  dry=echo' [dry] '
  echo '------------------------'
  echo "Dry run: Note that filenames may not match the actual files since we glob for"
  echo "         them. i.e. performing a sharp (non-dry) run would create new files"
  echo "         which would match the glob patterns we are using."
else
  dry=
fi


ensure_clean_working_revision


# Clean dist directories
if [ $GENERATE_BINARY -eq 1 ] || [ $GENERATE_SOURCE -eq 1 ]; then
  echo '------------------------'
  echo 'Cleaning dist dir...'
  $dry rm -vf dist/$PKG_DISTUTILS_ID*.tar.gz
  $dry rm -vf dist/ready/$PKG_ID*.tar.gz
  $dry mkdir -vp dist/ready
fi


# Build binary packages
if [ $GENERATE_BINARY -eq 1 ]; then
  for PYTHON in $@; do
    # Simple sanity check
    echo '------------------------'
    echo -n 'Building with '
    ($PYTHON -V) || exit 1
  
    # Run distutils
    $dry $PYTHON setup.py --quiet clean || exit 1
    $dry $PYTHON setup.py --quiet bdist --formats=gztar || exit 1

    # Rename resulting file
    PY_VER=$(echo $($PYTHON -V 2>&1) | sed 's/[^0-9\.]//g' | cut -d . -f 1,2)
    BDIST_FILE_ORG="$(basename "$(echo dist/${PKG_DISTUTILS_ID}*.tar.gz)")"
    # Convert smisk-1.0.0.system --> smisk-1.0.0-system and Add python version
    BDIST_FILE="$(echo "$BDIST_FILE_ORG" | sed 's/-'$VER'./-'$VER'-/' | sed 's/\.tar\.gz$/-py'$PY_VER'.tar.gz/')"
    if [ $IS_MILESTONE -eq 0 ]; then
      # smisk-1.0.0  -->  smisk-$PKG_VER
      BDIST_FILE="$(echo "$BDIST_FILE" | sed 's/-'$VER'/-'${PKG_VER}'/')"
    fi
    $dry mv -v "dist/$BDIST_FILE_ORG" "dist/ready/$BDIST_FILE" || exit 1
  done # end of each python env
fi


# Create source distribution
if [ $GENERATE_SOURCE -eq 1 ]; then
  echo '------------------------'
  echo 'Generating source package'
  $dry $DEFAULT_PYTHON setup.py --quiet sdist --formats=gztar || exit 1
  $dry mv -v "dist/${PKG_DISTUTILS_ID}.tar.gz" "dist/ready/${PKG_ID}.tar.gz"
fi


# Generate documentation
if [ $GENERATE_DOCS -eq 1 ]; then
  echo '------------------------'
  echo 'Generating documentation'
  
  PY_VER=$(echo $($DEFAULT_PYTHON -V 2>&1) | sed 's/[^0-9\.]//g' | cut -d . -f 1,2)
  BUILT_SMISK_DIR=$($DEFAULT_PYTHON -c "import os; print os.path.realpath('$(echo build/lib.*${PY_VER}/smisk)')")
  
  if ! ($DEFAULT_PYTHON -c 'import smisk,os,sys; sys.exit(not os.path.samefile(os.path.dirname(smisk.__file__), "'"$BUILT_SMISK_DIR"'"))' 2>/dev/null); then
    echo "$0: Warning: $BUILT_SMISK_DIR is not installed thus generating" >&2
    echo "  documentation would result in documentation for possibly another version." >&2
    if ! SMISK_DIR=$($DEFAULT_PYTHON -c 'import smisk,os; print os.path.dirname(smisk.__file__)' 2>/dev/null); then
      SMISK_DIR=$($DEFAULT_PYTHON -c 'import sys; print '%s/lib/python%s/smisk' % (sys.prefix, sys.version[:3])' 2>/dev/null)
    fi
    echo "  I suggest you:" >&2
    echo "    sudo ln -vfs \"$BUILT_SMISK_DIR\" \"$SMISK_DIR\"" >&2
    echo -n "$0: Warning: disabling generation" >&2
    GENERATE_DOCS=0
    if [ $DISTRIBUTE_DOCS -eq 1 ]; then
      echo -n " and distribution" >&2
      DISTRIBUTE_DOCS=0
    fi
    echo " of documentation." >&2
  fi
  
  if [ $GENERATE_DOCS -eq 1 ]; then
    # test again 'cus it might have changed in the test above
    $dry $DEFAULT_PYTHON setup.py apidocs
  fi
fi


# Things we need for any distribution
if [ $DISTRIBUTE_PKGS -eq 1 ] || [ $DISTRIBUTE_DOCS -eq 1 ]; then
  ISLOCALHOST=0
  if is_local_host $REMOTE_HOST; then ISLOCALHOST=1; fi
fi


# Distribute packages
if [ $DISTRIBUTE_PKGS -eq 1 ]; then
  echo '------------------------'
  echo "Distributing packages"
  CMD="cd $REMOTE_PATH;\
  for f in ${PKG_ID}*.tar.gz;do \
    if [ -f \"\$f\" ]; then\
      lname=\`echo \"\$f\" | sed 's/${PKG_VER}/latest/g'\`;\
      ln -sf \"\$f\" \"\$lname\";\
    fi;\
  done"
  echo -n "Copying dist/ready/${PKG_ID}*.tar.gz to "
  if [ $ISLOCALHOST -eq 1 ]; then
    echo $REMOTE_PATH
    $dry cp dist/ready/$PKG_ID*.tar.gz $REMOTE_PATH
    if [ $DISTRIBUTE_LINK_LATEST -eq 1 ]; then
      if [ $DRY_RUN -eq 1 ]; then
        $dry "echo $CMD | sh --verbose"
      else
        echo $CMD | sh --verbose || exit 1
      fi
    fi
  else
    echo "$REMOTE_HOST:$REMOTE_PATH"
    $dry scp -qC dist/ready/$PKG_ID*.tar.gz $REMOTE_HOST:$REMOTE_PATH || exit 1
    if [ $DISTRIBUTE_LINK_LATEST -eq 1 ]; then
      $dry ssh $REMOTE_HOST $CMD || exit 1
    fi
  fi
fi

# Distribute docs
if [ $DISTRIBUTE_DOCS -eq 1 ]; then
  echo '------------------------'
  echo "Distributing documentation"
  if [ $GENERATE_DOCS -eq 1 ] && [ ! -f doc/api/index.html ] && [ $DRY_RUN -eq 0 ]; then
    echo "$0: Warning: Documentation will not be distributed -- doc/api does not exist but was intended to be created." >&2
  else
    echo -n "Copying doc/api to "
    if [ $ISLOCALHOST -eq 1 ]; then
      echo "${REMOTE_PATH_DOCS}api"
      $dry cp -rf doc/api "${REMOTE_PATH_DOCS}api-new"
      $dry mv -vf "${REMOTE_PATH_DOCS}api-new" "${REMOTE_PATH_DOCS}api"
    else
      echo "$REMOTE_HOST:${REMOTE_PATH_DOCS}api"
      $dry scp -qCr doc/api "$REMOTE_HOST:${REMOTE_PATH_DOCS}api-new"
      $dry ssh $REMOTE_HOST "mv -vf ${REMOTE_PATH_DOCS}api-new ${REMOTE_PATH_DOCS}api"
    fi
  fi
fi


# End
if [ $DRY_RUN -eq 1 ]; then
  echo 'Done (dry run)'
else
  echo 'Done'
fi
exit 0
