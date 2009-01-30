#!/bin/sh
usage() { (cat <<USAGE
usage: $0 [--upload] [python]

Pack, sign and upload source distributions to python-smisk.org.
If you want to publish to PyPI, use the regular ./setup.py sdist command.

USAGE
  ) >&2
}

cd "$(dirname "$0")/.."
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then usage ; exit 1; fi

UPLOAD=0
if [ "$1" = "-u" ] || [ "$1" = "--upload" ]; then
  UPLOAD=1
fi

PYTHON=
if [ $# -gt 2 ]; then
  PYTHON="$2"
else
  PYTHON=$(/usr/bin/which python)
fi

rm -rf dist || exit 1
$PYTHON setup.py sdist || exit 1
FN=$( cd dist && echo smisk-*.tar.gz )
openssl dgst -md5 -hex "dist/$FN" | cut -d ' ' -f 2 > "dist/$FN.md5" || exit 1
openssl dgst -sha1 -hex "dist/$FN" | cut -d ' ' -f 2 > "dist/$FN.sha1" || exit 1
gpg --detach-sign --armor "dist/$FN" || exit 1

if [ $UPLOAD -eq 1 ]; then
  scp -C "dist/$FN"* "python-smisk.org:/var/www/python-smisk.org/www/public/dist/"
fi
