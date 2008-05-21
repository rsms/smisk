# encoding: utf-8
import time

class Timer(object):
  """
  A simple timer which can be used for low-precision benchmarking.
  """
  def __init__(self, start=True):
    self.t0 = 0.0
    self.t1 = 0.0
    if start:
      self.start()
  
  def start(self):
    self.t0 = time.time()
  
  def finish(self):
    self.t1 = time.time()
    return "%ds %dms %d\302\265s" % (self.seconds(), self.milli(), self.micro())
  
  def time(self):
    return self.t1 - self.t0
  
  def seconds(self):
    return int(self.time())
  
  def milli(self):
    return int(self.time() * 1000)
  
  def micro(self):
    return int(self.time() * 1000000)
  
