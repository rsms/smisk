#!/bin/sh
example="$1"
if [ "$example" == "" ]; then
  example="simple"
fi
cd examples/$example
echo 'Starting on http://localhost:8080/'
lighttpd -Df lighttpd.conf
