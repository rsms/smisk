#!/usr/bin/env python
# encoding: utf-8
import sys, os, socket
from datetime import datetime
from smisk import *

class MyApp(Application):
  # This is used to simulate processes dying for testing failover.
  # Set to -1 to disable
  die_after_num_requests = 4
  
  def __init__(self):
    Application.__init__(self)
    self.time_started = datetime.now()
  
  def service(self):
    self.response.headers = ["Content-Type: text/plain"]
    
    response(
      "This comes from a separately running process.\n\n",
      "Host:          %s\n" % socket.getfqdn(),
      "Listening on:  %s\n" % listening(),
      "Process id:    %d\n" % os.getpid(),
      "Process owner: %s\n" % os.getenv('USER'),
      "Time started:  %s\n" % self.time_started.strftime('%Y-%m-%d %H:%M:%S')
    )
    
    if self.die_after_num_requests != -1:
      self.die_after_num_requests -= 1
      if self.die_after_num_requests == 0:
        self.exit()
  

def main(argv):
  if len(argv) > 1:
    if argv[1] == '-h' or argv[1] == '--help':
      sys.stderr.write("usage: %s [address]\n" % argv[0])
      sys.stderr.write("example: %s 127.0.0.1:5000\n" % argv[0])
      sys.exit(1)
    bind(argv[1])
  else:
    bind("*:5000")
  MyApp().run()


if __name__ == '__main__':
  try:
    main(sys.argv)
  except KeyboardInterrupt:
    pass
