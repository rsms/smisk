#!/bin/sh
#
# Example usage:
#  ./log_usage.sh 1234|tee smisk_usage.log
#
cd $(dirname "$0")
. functions.sh

if [ $# -lt 2 ]; then
  echo "usage: $0 PID INTERVAL" >&2
  exit 1
fi
PID=$1
INTERVAL=$2
if [ ! -d /proc/$PID ]; then
  echo "/proc/$PID not found - wrong PID?" >&2
  echo "usage: $0 PID" >&2
  exit 1
fi
while true; do
  get_rss $PID;
  sleep $INTERVAL;
done
