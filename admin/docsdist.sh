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

VER=$(./setup.py --version)
REMOTEDIR="/var/www/python-smisk.org/www/public/docs"
TFN=".uploading-$(date '+%y%m%d-%H%M%S')-$VER"
echo "Uploading HTML docs to python-smisk.org:$REMOTEDIR/$TFN"
scp -Cr "docs/html" "python-smisk.org:$REMOTEDIR/$TFN" || exit 1
echo "Upload done. Staging new files $REMOTEDIR/$TFN -> $REMOTEDIR/$VER"
ssh python-smisk.org "cd $REMOTEDIR && mv -f $VER .$VER && (mv -f $TFN $VER && rm -rf .$VER) || mv -f .$VER $VER" || exit 1

echo "If you wish to make this documentation the current one, do this:"
echo "  ssh python-smisk.org 'cd $REMOTEDIR && rm -f current ; ln -sf $VER current'"
