# encoding: utf-8
import sys, os, time, threading, thread, logging, imp
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
  

def to_bool(o):
  if type(o) in (str, unicode, basestring):
    try:
      return int(o)
    except ValueError:
      o = o.lower()
      return o == 'true' or o == 'yes' or o == 'on' or o == 'enabled'
  else:
    return o

def wrap_exc_in_callable(exc):
  '''Wrap exc in a anonymous function, for later raising.
  
  :rtype: callable
  '''
  def a(*args, **kwargs):
    raise exc
  return a

def tokenize_path(path):
  '''Deconstruct a URI path into standardized tokens.
  
  :param path: A pathname
  :type  path: string
  :rtype: list'''
  tokens = []
  for tok in strip_filename_extension(path).split('/'):
    tok = URL.decode(tok)
    if len(tok):
      tokens.append(tok)
  return tokens

def strip_filename_extension(fn):
  '''Remove any file extension from filename.
  
  :rtype: string
  '''
  try:
    return fn[:fn.rindex('.')]
  except:
    return fn

def load_modules_in_dir(path, skip__init__=True):
  '''Import all modules in a directory.
  
  :returns: A list of modules imported
  :rtype:   list'''
  loaded = []
  for f in os.listdir(path):
    name = strip_filename_extension(f)
    if skip__init__ and name == '__init__':
      continue
    if f[0] != '.' and f[-3:] in ('.py', 'pyc') and f not in loaded:
      fp, pathname, desc = imp.find_module(name, [path])
      try:
        imp.load_module(name, fp, pathname, desc)
      finally:
        if fp:
          fp.close()
      loaded.append(f)
  return loaded

def normalize_url(url):
  ''':rtype: string'''
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
  ''':rtype: list'''
  s = []
  for t in v:
    s.append(t.__module__)
  s = list_unique_wild(s)
  s.sort()
  return s


def list_python_filenames_in_dir(path, only_py=True):
  ''':rtype: list'''
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
  '''Returns a list of all modules in which cls and any subclasses are defined.
  
  :rtype: list
  '''
  if exclude_root:
    modules = []
  else:
    try:
      modules = [sys.modules[cls.__module__]]
    except KeyError:
      modules = [__import__(cls.__module__, globals(), locals())]
  for subcls in cls.__subclasses__():
    modules.extend(find_modules_for_classtree(subcls, False, False))
  if unique:
    modules = list_unique(modules)
  return modules


def inspect(o, as_string=True):
  '''Returns a dictionary or string of all members and their values in object `o`.
  
  :param o:         Object to inspect
  :type  o:         object
  :param as_string: Return a string formatted KEY=VALUE\\n...
  :type  as_string: bool
  :returns: string or dict
  :rtype: object
  '''
  items = {}
  for k in dir(o):
    items[k] = eval('o.'+k)
  if as_string:
    return "\n".join(['%s=%r' % kv for kv in items.items()])
  return items


def list_unique_wild(seq):
  '''
  :param seq:
  :type  seq: list
  :rtype: list'''
  # Not order preserving but faster than list_unique
  return list(set(seq))


def list_unique(seq):
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
  
  :param s:
  :type  s: list
  :rtype: list
  '''
  n = len(seq)
  if n == 0:
    return []
  # Try using a dict first, as that's the fastest and will usually
  # work.  If it doesn't work, it will usually fail quickly, so it
  # usually doesn't cost much to *try* it.  It requires that all the
  # sequence elements be hashable, and support equality comparison.
  u = {}
  try:
    for x in seq:
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
    t = list(seq)
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
  for x in seq:
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
