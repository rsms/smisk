# encoding: utf-8
'''thread
'''
import threading, thread, logging

__all__ = ['PerpetualTimer', 'Monitor']
log = logging.getLogger(__name__)

class PerpetualTimer(threading._Timer):
  '''A subclass of threading._Timer whose run() method repeats.'''
  ident = None
  ''':type: int'''
  
  def __init__(self, frequency, callback, setup_callback=None, *args, **kwargs):
    threading._Timer.__init__(self, frequency, callback, *args, **kwargs)
    self.setup_callback = setup_callback
  
  def run(self):
    self.ident = thread.get_ident()
    if self.setup_callback is not None:
      self.setup_callback()
    while True:
      self.finished.wait(self.interval)
      if self.finished.isSet():
        return
      self.function(*self.args, **self.kwargs)
  


class Monitor(object):
  '''Periodically run a callback in its own thread.'''
  frequency = 60.0
  ''':type: float'''
  
  def __init__(self, callback, setup_callback=None, frequency=60.0):
    self.callback = callback
    self.setup_callback = setup_callback
    self.frequency = frequency
    self.thread = None
  
  def start(self):
    '''Start our callback in its own perpetual timer thread.'''
    if self.frequency > 0:
      threadname = "Monitor:%s" % self.__class__.__name__
      if self.thread is None:
        self.thread = PerpetualTimer(self.frequency, self.callback, self.setup_callback)
        self.thread.setName(threadname)
        self.thread.start()
        log.debug("Started thread %r", threadname)
      else:
        log.debug("Thread %r already started", threadname)
  start.priority = 70
  
  def stop(self):
    '''Stop our callback's perpetual timer thread.'''
    if self.thread is None:
      log.warn("No thread running for %s", self)
    else:
      # Note: For some reason threading._active dict freezes in some conditions
      # here, so we compare thread ids rather than comparing using threading.currentThread.
      if self.thread.ident != thread.get_ident():
        self.thread.cancel()
        self.thread.join()
        log.debug("Stopped thread %r", self.thread.getName())
      self.thread = None
  
  def restart(self):
    '''Stop the callback's perpetual timer thread and restart it.'''
    self.stop()
    self.start()
  
