# encoding: utf-8
import sys, os, time, threading, thread, logging
from smisk.core import Application, URL

None2 = (None, None)
''':type: tuple'''

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
  frequency = 60
  
  def __init__(self, callback, setup_callback=None, frequency=60):
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
  


class Timer(object):
  '''A simple universal timer.'''
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
  

def wrap_exc_in_callable(exc):
  '''Wrap exc in a anonymous function, for later raising.'''
  def a(*args, **kwargs):
    raise exc
  return a

def tokenize_path(path):
  '''Deconstruct a URI path into standardized tokens.
  
  :param path: A pathname
  :type  path: string
  :rtype: list'''
  tokens = []
  for tok in path.split('/'):
    tok = URL.decode(tok)
    if len(tok):
      tokens.append(tok)
  if tokens:
    tokens[-1] = strip_filename_extension(tokens[-1])
  return tokens

def strip_filename_extension(fn):
  '''Remove any file extension from filename.'''
  try:
    return fn[:fn.rindex('.')]
  except:
    return fn

def normalize_url(url):
  if url.find('://') == -1:
    # url is actually a path
    path = url
    url = Application.current().request.url
    if len(path) == 0:
      path = '/'
    elif path[0] != '/':
      path = os.path.normpath(url.path) + '/' + os.path.normpath(path)
    else:
      path = os.path.normpath(path)
    url = url.to_s(port=url.port!=80, path=False) + path
  return url


def unique_sorted_modules_of_items(v):
  s = []
  for t in v:
    s.append(t.__module__)
  s = list_unique_wild(s)
  s.sort()
  return s


def list_python_filenames_in_dir(path, only_py=True):
  names = []
  for fn in os.listdir(path):
    if fn[-3:] == '.py':
      names.append(fn[:-3])
    elif not only_py:
      fn4 = fn[-4:]
      if fn4 == '.pyc' or fn4 == '.pyo':
        names.append(fn[:-4])
  if names:
    if not only_py:
      names = list_unique_wild(names)
    names.sort()
  return names


def find_modules_for_classtree(cls, exclude_root=True, unique=True):
  '''
  Returns a list of all modules in which cls and any subclasses are defined.
  '''
  if exclude_root:
    modules = []
  else:
    modules = [sys.modules[cls.__module__]]
  for subcls in cls.__subclasses__():
    modules.extend(find_modules_for_classtree(subcls, False, False))
  if unique:
    modules = list_unique(modules)
  return modules


def list_unique_wild(seq):
  # Not order preserving but faster than list_unique
  return list(set(seq))


def list_unique(s):
  '''Return a list of the elements in s, but without duplicates.
  
  For example, unique([1,2,3,1,2,3]) is some permutation of [1,2,3],
  unique("abcabc") some permutation of ["a", "b", "c"], and
  unique(([1, 2], [2, 3], [1, 2])) some permutation of
  [[2, 3], [1, 2]].
  
  For best speed, all sequence elements should be hashable.  Then
  unique() will usually work in linear time.
  
  If not possible, the sequence elements should enjoy a total
  ordering, and if list(s).sort() doesn't raise TypeError it's
  assumed that they do enjoy a total ordering.  Then unique() will
  usually work in O(N*log2(N)) time.
  
  If that's not possible either, the sequence elements must support
  equality-testing.  Then unique() will usually work in quadratic
  time.
  '''
  n = len(s)
  if n == 0:
    return []
  # Try using a dict first, as that's the fastest and will usually
  # work.  If it doesn't work, it will usually fail quickly, so it
  # usually doesn't cost much to *try* it.  It requires that all the
  # sequence elements be hashable, and support equality comparison.
  u = {}
  try:
    for x in s:
      u[x] = 1
  except TypeError:
    del u  # move on to the next method
  else:
    return u.keys()
  # We can't hash all the elements.  Second fastest is to sort,
  # which brings the equal elements together; then duplicates are
  # easy to weed out in a single pass.
  # NOTE:  Python's list.sort() was designed to be efficient in the
  # presence of many duplicate elements.  This isn't true of all
  # sort functions in all languages or libraries, so this approach
  # is more effective in Python than it may be elsewhere.
  try:
    t = list(s)
    t.sort()
  except TypeError:
    del t  # move on to the next method
  else:
    assert n > 0
    last = t[0]
    lasti = i = 1
    while i < n:
      if t[i] != last:
        t[lasti] = last = t[i]
        lasti += 1
      i += 1
    return t[:lasti]
  
  # Brute force is all that's left.
  u = []
  for x in s:
    if x not in u:
      u.append(x)
  return u


def format_exc(exc=None):
  ''':rtype: string'''
  if exc is None:
    exc = sys.exc_info()
  if exc == (None, None, None):
    return ''
  import traceback
  return ''.join(traceback.format_exception(*exc))
