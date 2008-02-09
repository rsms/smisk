#!/usr/bin/env python
# encoding: utf-8
import sys, os, time
import process

if __name__ == '__main__':
  if len(sys.argv) < 3 or (sys.argv[1] == '-h' or sys.argv[1] == '--help'):
    sys.stderr.write("usage: %s startport numchilds [bindhost]\n" % sys.argv[0])
    sys.stderr.write("example: %s 5000 5 127.0.0.1\n" % sys.argv[0])
    sys.exit(1)
  bindhost = ''
  if len(sys.argv) > 3:
    bindhost = sys.argv[3]
  startport = int(sys.argv[1])
  numchilds = int(sys.argv[2])
  children = []
  for n in xrange(numchilds):
    port = startport + n
    pid = os.fork()
    if pid == 0:
      try:
        process.main((sys.argv[0], '%s:%d' % (bindhost, port)))
      except KeyboardInterrupt:
        pass
      sys.exit(0)
    else:
      children.append(pid)
      print 'Forked #%d listening on %s:%d' % (pid, bindhost, port)
  try:
    for pid in children:
      print "Child #%d exited with status %d" % os.waitpid(pid, 0)
  except KeyboardInterrupt:
    print 'Stopping child processes...'
    for pid in children:
      os.kill(pid, 2)
      print "#%d exited with status %d" % os.waitpid(pid, 0)
  
