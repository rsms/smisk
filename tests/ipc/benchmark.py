#!/usr/bin/env python
# encoding: utf-8
import sys, os, time, random
from smisk.util.benchmark import benchmark
import smisk.ipc

def main():
  from optparse import OptionParser
  parser = OptionParser()
  
  parser.add_option("-t", "--sync-time", dest="sync_time",
                  help="Start benchmark at specified time, formatted HH:MM[:SS]. Disabled by default.", 
                  metavar="TIME", default=None)
  
  parser.add_option("-i", "--iterations", dest="iterations",
                  help="Number of iterations to perform. Defaults to 100 000", 
                  metavar="N", default=100000, type='int')
  
  parser.add_option("-d", "--idle", dest="idle",
                  help="Milliseconds to idle between operations. Defaults to 0 (disabled).", 
                  metavar="MS", default=0, type='int')
  
  parser.add_option("-r", "--read",
                  action="store_true", dest="read", default=False,
                  help="Perform reading")
  
  parser.add_option("-w", "--write",
                  action="store_true", dest="write", default=False,
                  help="Perform writing")
  
  parser.add_option("-c", "--cdb",
                  action="store_true", dest="cdb", default=False,
                  help="Use lock-free CDB (one writer/multiple readers).")
  
  (options, args) = parser.parse_args()
  
  if not options.read and not options.write:
    print >> sys.stderr, 'Neither --write nor --read was specified'\
      ' -- automatically enabling both'
    options.read = True
    options.write = True
  
  store = smisk.ipc.shared_dict()
  idle_sec = float(options.idle) / 1000.0
  
  if options.sync_time:
    timestr = time.strftime('%Y%d%m') + options.sync_time
    try:
      options.sync_time = time.strptime(timestr, '%Y%d%m%H:%M:%S')
    except ValueError:
      try:
        options.sync_time = time.strptime(timestr, '%Y%d%m%H:%M')
      except ValueError:
        raise ValueError('time does not match format: HH:MM[:SS]')
    sync_t = time.mktime(options.sync_time)
    
    if sync_t > time.time():
      print 'Waiting for time sync %s' % time.strftime('%H:%M:%S', options.sync_time)
      last_printed_second = 0
      while 1:
        t = time.time()
        if sync_t <= t:
          break
        ti = int(sync_t - t)
        if ti and ti != last_printed_second:
          last_printed_second = ti
          sys.stdout.write('%d ' % ti)
          sys.stdout.flush()
        time.sleep(0.01)
      sys.stdout.write('\n')
      sys.stdout.flush()
  
  rw = 'write'
  if options.read and options.write:
    rw = 'write+read'
  elif options.read:
    rw = 'read'
  
  pid = os.getpid()
  time.sleep(0.1 * random.random())
  
  idle_msg = ''
  if idle_sec > 0.0:
    idle_msg = ' with a per-iteration idle time of %.0f ms' % (idle_sec * 1000.0)
  print 'Benchmarking %d iterations of %s#%d%s' % (options.iterations, rw, pid, idle_msg)
  
  if options.read and options.write:
    for x in benchmark('%s#%d' % (rw, pid), options.iterations, it_subtractor=idle_sec):
      store['pid'] = pid
      time.sleep(idle_sec)
      pid_found = store['pid']
  elif options.read:
    for x in benchmark('%s#%d' % (rw, pid), options.iterations, it_subtractor=idle_sec):
      time.sleep(idle_sec)
      pid_found = store['pid']
  else:
    for x in benchmark('%s#%d' % (rw, pid), options.iterations, it_subtractor=idle_sec):
      time.sleep(idle_sec)
      store['pid'] = pid


if __name__ == '__main__':
  main()
