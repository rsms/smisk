#!/bin/sh
cd `dirname "$0"`/..
echo 'Starting on http://localhost:8080/'
lighttpd -Df config/lighttpd.conf
