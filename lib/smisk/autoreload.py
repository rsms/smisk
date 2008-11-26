# encoding: utf-8
'''Automatically reload processes when components are updated.
'''
import sys, os, logging, re
from smisk.util.threads import Monitor
from smisk.config import config

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
    self.config_files = set()
    self.mtimes = {}
    self.log = None # in runner thread -- should not be set manually
    self.match = match
    Monitor.__init__(self, self.run, self.setup, frequency)
  
  def start(self):
    '''Start our own perpetual timer thread for self.run.'''
    if self.thread is None:
      self.mtimes = {}
    self._update_config_files_list()
    Monitor.start(self)
  start.priority = 70 
  
  def _update_config_files_list(self):
    config_files = set()
    if config.get('smisk.autoreload.config', config.get('smisk.autoreload')):
      for path,conf in config.sources:
        if path[0] != '<':
          config_files.add(path)
    self.config_files = config_files
  
  def setup(self):
    self.log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
  
  def on_module_modified(self, path):
    # The file has been deleted or modified.
    self.log.info("%s was modified", path)
    self.thread.cancel()
    self.log.debug("Stopped autoreload monitor (thread %r)", self.thread.getName())
    import smisk.core
    smisk.core.app.exit()
  
  def on_config_modified(self, path):
    config.reload()
    self._update_config_files_list()
      
  def run(self):
    '''Reload the process if registered files have been modified.'''
    sysfiles = set()
    
    if config.get('smisk.autoreload.modules', config.get('smisk.autoreload')):
      for k, m in sys.modules.items():
        if self.match is None or self.match.match(k):
          if hasattr(m, '__loader__'):
            if hasattr(m.__loader__, 'archive'):
              k = m.__loader__.archive
          k = getattr(m, '__file__', None)
          sysfiles.add(k)
    
    for path in sysfiles | self.config_files:
      if path:
        if path.endswith('.pyc') or path.endswith('.pyo'):
          path = path[:-1]
        
        oldtime = self.mtimes.get(path, 0)
        if oldtime is None:
          # Module with no .py file. Skip it.
          continue
        
        #self.log.info('Checking %r' % sysfiles)
        
        try:
          mtime = os.stat(path).st_mtime
        except OSError:
          # Either a module with no .py file, or it's been deleted.
          mtime = None
        
        if path not in self.mtimes:
          # If a module has no .py file, this will be None.
          self.mtimes[path] = mtime
        else:
          #self.log.info("checking %s", path)
          if mtime is None or mtime > oldtime:
            if path.endswith(config.filename_ext) and path in [k for k,d in config.sources]:
              self.on_config_modified(path)
              self.mtimes[path] = mtime
            else:
              self.on_module_modified(path)
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
  
