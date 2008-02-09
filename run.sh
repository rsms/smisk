#!/bin/sh
path="$1"
if [ "$path" == "" ]; then
  path="examples/simple"
fi
cd $path
echo 'Starting on http://localhost:8080/'
lighttpd -Df lighttpd.conf
