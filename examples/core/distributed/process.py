#!/usr/bin/env python
# encoding: utf-8
import sys, os, socket
from datetime import datetime
from smisk.core import *

class MyApp(Application):
  # This is used to simulate processes dying for testing failover.
  # Set to -1 to disable
  die_after_num_requests = -1
  
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
      "Time started:  %s\n" % self.time_started.strftime('%Y-%m-%d %H:%M:%S'),
      "\n",
      "self.request.url: %r\n" % self.request.url,
      "self.request.env: %r\n" % self.request.env
    )
    
    if self.die_after_num_requests != -1:
      self.die_after_num_requests -= 1
      if self.die_after_num_requests == 0:
        self.exit()
  

if __name__ == '__main__':
  from smisk.util.main import main
  main(MyApp)
