#!/usr/bin/env python
# encoding: utf-8
# 
# Concurrent Data Store test app
# 
# http://www.oracle.com/technology/documentation/berkeley-db/db/ref/cam/intro.html
# 

import sys, os, time, random
import smisk.ipc.bsddb

def main():
  from optparse import OptionParser
  parser = OptionParser()
  
  parser.add_option("-i", "--random-idle", dest="idle",
                  help="Milliseconds to idle between operations, randomized 0-1. Defaults to 100.",
                  metavar="MS", default=100, type='int')
  
  parser.add_option("-r", "--read",
                  action="store_true", dest="read", default=False,
                  help="Perform reading")
  
  parser.add_option("-w", "--write",
                  action="store_true", dest="write", default=False,
                  help="Perform writing")
  
  parser.add_option("-d", "--detect",
                  action="store_true", dest="detect_concurrance", default=False,
                  help="When concurrance is detected, print info to stdout. Implies -r and -w")
  
  (options, args) = parser.parse_args()
  
  if not options.read and not options.write:
    options.read = True
  
  store = smisk.ipc.bsddb.shared_dict()
  idle_sec = float(options.idle) / 1000.0
  
  if options.detect_concurrance:
    options.write = True
    options.read = True
  
  rw = 'write'
  if options.read and options.write:
    rw = 'write+read'
  elif options.read:
    rw = 'read'
  
  pid = os.getpid()
  
  idle_msg = ''
  if idle_sec > 0.0:
    idle_msg = ' with randomized iteration idle time: 0.0-%.0f ms' % (idle_sec * 1000.0)
  print '[%d] Running %s%s' % (pid, rw, idle_msg)
  
  while 1:
    if options.write:
      time.sleep(random.random()*idle_sec)
      store['pid'] = pid
    if options.read:
      time.sleep(random.random()*idle_sec)
      try:
        pid_found = store['pid']
      except KeyError:
        pass
    if options.detect_concurrance and pid_found != pid:
      print '[%d] Concurrance detected -- #%d wrote in between' % (pid, pid_found)


if __name__ == '__main__':
  main()
