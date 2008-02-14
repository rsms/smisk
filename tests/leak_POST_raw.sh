#!/bin/sh
BASEDIR=$(dirname "$0")/..

. "$BASEDIR/debug/functions.sh"

_request() {
  make_request "--data-binary 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' --header 'Content-Type: text/plain'"
}

lighty_start "$BASEDIR/examples/input"
PROCESS_PID=$(ps_find_pid examples/input/process.py)

RSS1=$(get_rss $PROCESS_PID)

for (( i=0; i<10; i++ )); do
  _request
done
RSS2=$(get_rss $PROCESS_PID)

for (( i=0; i<10; i++ )); do
  _request
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
  echo "after 200r: $RSS3 KB"
  lighty_stop
  exit 1
fi
