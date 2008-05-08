#!/bin/sh
cd $(dirname "$0")
if [ $# -eq 0 ]; then
  cd examples/simple
else
  if [ ! -f "$1/lighttpd.conf" ]; then
    echo "$1 does not contain a lighttpd.conf file" >&2
    exit 1
  fi
  cd "$1"
fi
echo 'Starting on http://localhost:8080/'
lighttpd -Df lighttpd.conf
