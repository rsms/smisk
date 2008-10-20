# encoding: utf-8
'''Miscellaneous utilities.
'''
import sys, os, time, threading, thread, logging, imp
try:
  import reprlib
except ImportError:
  import repr as reprlib
from smisk.core import Application, URL

None2 = (None, None)
''':type: tuple'''

log = logging.getLogger(__name__)


class NamedObject:
  '''General purpose named object.
  '''
  def __init__(self,name):
    self.name = name
  
  def __repr__(self):
    return self.name
  

Undefined = NamedObject('Undefined')
'''Indicates an undefined value.
'''


class frozendict(dict):
  '''Immutable dictionary.
  '''
  def __setitem__(self, *args, **kwargs):
    raise TypeError("'frozendict' object does not support item assignment")
  
  setdefault = __delitem__ = clear = pop = popitem = __setitem__
  
  def update(self, *args):
    '''Update a mutable copy with key/value pairs from b, replacing existing keys.
    
    :returns: A mutable copy with updated pairs.
    :rtype: dict
    '''
    d = self.copy()
    d.update(*args)
    return d
  
  copy = dict.copy
  '''Returns a mutable copy.
  '''
  
  def __hash__(self):
    items = self.items()
    res = hash(items[0])
    for item in items[1:]:
        res ^= hash(item)
    return res
  


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
  


class introspect(object):    
  VARARGS = 4
  KWARGS = 8
  
  _repr = reprlib.Repr()
  _repr.maxlong = 100
  _repr.maxstring = 200
  _repr.maxother = 200
  
  @classmethod
  def callable_info(cls, f):
    '''Info about a callable.
    
    The results are cached for efficiency.
    
    :param f:
    :type  f: callable
    :rtype: frozendict
    '''
    try:
      f = f.im_func
    except AttributeError:
      try:
        f.func_code
      except AttributeError:
        f = f.__call__
    try:
      return f.info
    except AttributeError:
      pass
    args = []
    code = f.func_code
    arglist = list(code.co_varnames[:code.co_argcount][1:])
    varargs = False
    kwargs = False
    if code.co_flags & cls.VARARGS:
      varargs = True
    if code.co_flags & cls.KWARGS:
      kwargs = True
    arglist_len = len(arglist)
    co_locals = []
    if arglist_len < code.co_argcount:
      for i,n in enumerate(code.co_varnames[arglist_len+1:]):
        co_locals.append(n)
    func_defaults_len = 0
    if f.func_defaults:
      func_defaults_len = len(f.func_defaults)
    for i,n in enumerate(arglist):
      default_index = i-(arglist_len-func_defaults_len)
      v = Undefined
      if default_index > -1:
        v = f.func_defaults[default_index]
      args.append((n, v))
    f.info = frozendict({
      'name':f.func_name,
      'args':args,
      'varargs':varargs,
      'kwargs':kwargs,
      'locals':tuple(co_locals)
    })
    return f.info
  
  @classmethod
  def format_members(cls, o):
    s = []
    longest_k = 0
    for k in dir(o):
      if len(k) > longest_k:
        longest_k = len(k)
    pat = '%%-%ds = %%s' % longest_k
    for k in dir(o):
      s.append(pat % (k, cls._repr.repr(getattr(o,k))))
    return '\n'.join(s)
  
  @classmethod
  def ensure_va_kwa(cls, f, parent=None):
    '''Ensures `f` accepts both ``*varargs`` and ``**kwargs``.
    
    If `f` does not support ``*args``, it will be wrapped with a
    function which cuts away extra arguments in ``*args``.
    
    If `f` does not support ``*args``, it will be wrapped with a
    function which discards the ``**kwargs``.
    
    :param f:
    :type  f:       callable
    :param parent:  The parent on which `f` is defined. If specified, we will perform
                    ``parent.<name of f> = wrapper`` in the case we needed to wrap `f`.
    :type  parent:  object
    :returns: A callable which is guaranteed to accept both ``*args`` and ``**kwargs``.
    :rtype: callable
    '''
    info = cls.callable_info(f)
    va_kwa_wrapper = None
    if not info['varargs'] and not info['kwargs']:
      def va_kwa_wrapper(*args, **kwargs):
        return f(*args[:len(info['args'])])
    elif not info['varargs']:
      def va_kwa_wrapper(*args, **kwargs):
        return f(*args[:len(info['args'])], **kwargs)
    elif not info['kwargs']:
      def va_kwa_wrapper(*args, **kwargs):
        return f(*args)
    if va_kwa_wrapper:
      va_kwa_wrapper.info = frozendict(info.update({
        'varargs': True,
        'kwargs': True
      }))
      try:
        va_kwa_wrapper.im_class = f.im_class
        va_kwa_wrapper.im_func = f
      except AttributeError:
        pass
      for k in dir(f):
        if k[0] != '_' or k in ('__name__'):
          setattr(va_kwa_wrapper, k, getattr(f, k))
      if parent is not None:
        setattr(parent, info['name'], va_kwa_wrapper)
      return va_kwa_wrapper
    return f
  


repr2 = introspect._repr.repr
'''Limited ``repr``, only printing up to 4-6 levels and 100 chars per entry.

:type: repr.Repr
'''


def classmethods(cls):
  '''List names of all class methods in class `cls`.
  
  :rtype: list
  '''
  return [k for k in dir(cls) \
    if (k[0] != '_' and getattr(getattr(cls, k), 'im_class', None) == type)]


def parse_qvalue_header(s, accept_any_equals='*/*', partial_endswith='/*'):
  '''Parse a qvalue HTTP header'''
  vqs = []
  highqs = []
  partials = []
  accept_any = False
  
  if not partial_endswith:
    partial_endswith = None
  
  for part in s.split(','):
    part = part.strip(' ')
    p = part.find(';')
    if p != -1:
      # todo Find out what the undocumented, but revealed, level= tags in HTTP 1.1 
      #      really mean and if they exists in reality. As they are not documented,
      #      we will not implement support for it. [RFC 2616, chapter 14.1 "Accept"]
      pp = part.find('q=', p)
      if pp != -1:
        q = int(float(part[pp+2:])*100.0)
        part = part[:p]
        vqs.append([part, q])
        if q == 100:
          highqs.append(part)
        continue
    # No qvalue; we use three classes: any (q=0), partial (q=50) and complete (q=100)
    qual = 100
    if part == accept_any_equals:
      qual = 0
      accept_any = True
    else:
      if partial_endswith is not None and part.endswith('/*'):
        partial = part[:-2]
        if not partial:
          continue
        qual = 50
        partials.append(partial) # remove last char '*'
      else:
        highqs.append(part)
    vqs.append([part, qual])
  # Order by qvalue
  vqs.sort(lambda a,b: b[1] - a[1])
  return vqs, highqs, partials, accept_any


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
  def exc_wrapper(*args, **kwargs):
    raise exc
  return exc_wrapper

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
    if f[0] != '.' and f[-3:] in ('.py', 'pyc') and name not in loaded:
      fp, pathname, desc = imp.find_module(name, [path])
      try:
        imp.load_module(name, fp, pathname, desc)
      finally:
        if fp:
          fp.close()
      loaded.append(name)
  return loaded

def normalize_url(url):
  ''':rtype: string'''
  if url.find('://') == -1:
    # url is actually a path
    path = url
    url = Application.current.request.url
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
  
  :param seq:
  :type  seq: list
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


def format_exc(exc=None, as_string=False):
  ''':rtype: string'''
  if exc is None:
    exc = sys.exc_info()
  if exc == (None, None, None):
    return ''
  import traceback
  if as_string:
    return ''.join(traceback.format_exception(*exc))
  else:
    return traceback.format_exception(*exc)
