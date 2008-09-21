# encoding: utf-8
import sys, os, logging, re
from smisk.util import Monitor

log = logging.getLogger(__name__)


class Autoreloader(Monitor):
  '''Reloads application when files change'''
  
  frequency = 1
  match = None
  
  def __init__(self, frequency=1, match=None):
    '''
    :param frequency: How often to perform file modification checks
    :type  frequency: int
    :param match:     Only check modules matching this regular expression.
                      Matches anything if None.
    :type  match:     re.RegExp
    '''
    self.files = set()
    self.mtimes = {}
    self.log = None # in runner thread -- should not be set manually
    self.match = match
    Monitor.__init__(self, self.run, self.setup, frequency)
  
  def start(self):
    '''Start our own perpetual timer thread for self.run.'''
    if self.thread is None:
      self.mtimes = {}
    Monitor.start(self)
  start.priority = 70 
  
  def setup(self):
    self.log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
  
  def run(self):
    '''Reload the process if registered files have been modified.'''
    sysfiles = set()
    for k, m in sys.modules.items():
      if self.match is None or self.match.match(k):
        if hasattr(m, '__loader__'):
          if hasattr(m.__loader__, 'archive'):
            k = m.__loader__.archive
        k = getattr(m, '__file__', None)
        sysfiles.add(k)
    
    for filename in sysfiles | self.files:
      if filename:
        if filename.endswith('.pyc') or filename.endswith('.pyo'):
          filename = filename[:-1]
        
        oldtime = self.mtimes.get(filename, 0)
        if oldtime is None:
          # Module with no .py file. Skip it.
          continue
        
        #self.log.info('Checking %r' % sysfiles)
        
        try:
          mtime = os.stat(filename).st_mtime
        except OSError:
          # Either a module with no .py file, or it's been deleted.
          mtime = None
        
        if filename not in self.mtimes:
          # If a module has no .py file, this will be None.
          self.mtimes[filename] = mtime
        else:
          #self.log.info("checking %s", filename)
          if mtime is None or mtime > oldtime:
            # The file has been deleted or modified.
            self.log.info("%s was modified", filename)
            self.thread.cancel()
            #self.log.debug("Stopped thread %r", self.thread.getName())
            import smisk.core
            smisk.core.Application.current().exit()
            #raise KeyboardInterrupt
            return
  

if __name__ == '__main__':
  logging.basicConfig(
    level=logging.DEBUG,
    format = '%(levelname)-8s %(name)-20s %(message)s',
    datefmt = '%d %b %H:%M:%S'
  )
  
  import time, smisk.core
  ar = Autoreloader()
  ar.start()
  time.sleep(4)
  print 'Stopping'
  ar.stop()
  
