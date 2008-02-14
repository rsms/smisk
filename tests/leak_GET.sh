#!/bin/sh
BASEDIR=$(dirname "$0")/..

. "$BASEDIR/debug/functions.sh"

lighty_start "$BASEDIR/examples/minimal"
PROCESS_PID=$(ps_find_pid examples/minimal/process.py)

RSS1=$(get_rss $PROCESS_PID)

for (( i=0; i<100; i++ )); do
  make_request
done
RSS2=$(get_rss $PROCESS_PID)

for (( i=0; i<300; i++ )); do
  make_request
done
RSS3=$(get_rss $PROCESS_PID)

if [ $RSS1 -lt $RSS2 ] && [ $RSS2 -eq $RSS3 ]; then
  echo PASS
  lighty_stop
  exit 0
else
  echo FAIL '[ $RSS1 -lt $RSS2 ] && [ $RSS2 -eq $RSS3 ]'
  echo "before:     $RSS1 KB"
  echo "after 100r: $RSS2 KB"
  echo "after 400r: $RSS3 KB"
  lighty_stop
  exit 1
fi
