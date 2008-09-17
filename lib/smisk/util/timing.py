# encoding: utf-8
import time

class Timer(object):
  """
  A simple real timer.
  """
  def __init__(self, start=True):
    self.t0 = 0.0
    self.t1 = 0.0
    self.seconds = self.time
    if start:
      self.start()
  
  def start(self):
    self.t0 = time.time()
  
  def finish(self):
    self.t1 = time.time()
    return "%.0fs %.0fms %.0fus" % (self.seconds(), self.milli(), self.micro())
  
  def time(self):
    return self.t1 - self.t0
  
  def seconds(self): # alias for time
    return self.time()
  
  def milli(self):
    return (self.time() * 1000) % 1000
  
  def micro(self):
    return (self.time() * 1000000) % 1000
  
