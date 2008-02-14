get_rss() { # int (int pid) - returns resident size in KB
  PID=$1
  if [ "$(uname -s)" == "Darwin" ]; then
    cat /proc/$PID/task/basic_info/resident_size|sed -E 's/[^0-9]//g';
  else # assume linux
    cat /proc/$PID/status|grep VmRSS:|sed -r 's/[^0-9]//g'
  fi
}

sleep_fine() {
  python -c 'import time;time.sleep('$1')'
}

ps_find_pid() { # (string grep_for_to_find)
  ps x|grep "$1"|grep -v "grep $1"|sed 's/^ *//g'|cut -d ' ' -f 1
}

lighty_start() { # (string in_directory)
  cd "$1"
  lighttpd -f lighttpd.conf
  sleep 1
  read LIGTHY_PID < server.pid
}

lighty_stop() {
  if [ "$LIGTHY_PID" != "" ]; then
    kill $LIGTHY_PID
    sleep 2
    kill -9 $LIGTHY_PID 2> /dev/null
    rm -f server.pid
  fi
}

make_request() { # (string extra_opts_to_curl)
  R=$(curl -i --silent $1 localhost:8080/receive)
  if [ "$(echo "$R"|grep 'HTTP/1.1 200 OK')" == "" ]; then
    echo 'Non-200 response: '$R >&2
    lighty_stop
    exit 1
  fi
}

