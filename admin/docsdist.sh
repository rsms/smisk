#!/bin/sh
usage() { (cat <<USAGE
usage: $0

Generate and upload documentation to python-smisk.org.

USAGE
  ) >&2
}

cd "$(dirname "$0")/.."
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then usage ; exit 1; fi

rm -rf docs/html || exit 1
./setup.py docs || exit 1

RV=$(./setup.py --release-version)
REMOTEDIR="/var/www/python-smisk.org/www/public/docs"
scp -Cr "docs/html" "python-smisk.org:${REMOTEDIR}/.${RV}"
ssh python-smisk.org "cd ${REMOTEDIR} && mv -f .${RV} ${RV}"

echo "If you wish to make this documentation the current one, do this:"
echo "  ssh python-smisk.org 'cd ${REMOTEDIR} && ln -sf ${RV} current'"
