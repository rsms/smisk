# encoding: utf-8
'''Miscellaneous utilities.
'''
import sys, os, time, threading, thread, logging, imp, inspect, re
from datetime import datetime, timedelta, tzinfo
ZERO_TIMEDELTA = timedelta(0)
try:
  import reprlib
except ImportError:
  import repr as reprlib
from smisk.core import Application, URL
from types import *

None2 = (None, None)
''':type: tuple
'''

RegexType = type(re.compile('.'))
''':type: type
'''

_log = logging.getLogger(__name__)


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
        _log.debug("Started thread %r", threadname)
      else:
        _log.debug("Thread %r already started", threadname)
  start.priority = 70
  
  def stop(self):
    '''Stop our callback's perpetual timer thread.'''
    if self.thread is None:
      _log.warn("No thread running for %s", self)
    else:
      # Note: For some reason threading._active dict freezes in some conditions
      # here, so we compare thread ids rather than comparing using threading.currentThread.
      if self.thread.ident != thread.get_ident():
        self.thread.cancel()
        self.thread.join()
        _log.debug("Stopped thread %r", self.thread.getName())
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
  
  _info_cache = {}
  
  @classmethod
  def callable_info(cls, f):
    '''Info about a callable.
    
    The results are cached for efficiency.
    
    :param f:
    :type  f: callable
    :rtype: frozendict
    '''
    if not callable(f):
      return None
    
    if isinstance(f, FunctionType):
      # in case of ensure_va_kwa
      try:
        f = f.wrapped_func
      except AttributeError:
        pass
    
    cache_key = callable_cache_key(f)
    
    try:
      return cls._info_cache[cache_key]
    except KeyError:
      pass
    
    if not isinstance(f, (MethodType, FunctionType)):
      try:
        f = f.__call__
      except AttributeError:
        return None
    
    args, varargs, varkw, defaults = inspect.getargspec(f)
    method = False
    
    if isinstance(f, MethodType):
      # Remove self
      args = args[1:]
      method = True
    
    _args = []
    args_len = len(args)
    defaults_len = 0
    
    if defaults is not None:
      defaults_len = len(defaults)
    
    for i,n in enumerate(args):
      default_index = i-(args_len-defaults_len)
      v = Undefined
      if default_index > -1:
        v = defaults[default_index]
      _args.append((n, v))
    
    info = frozendict({
      'name':f.func_name,
      'args':tuple(_args),
      'varargs':bool(varargs),
      'varkw':bool(varkw),
      'method':method
    })
    
    cls._info_cache[cache_key] = info
    return info
  
  
  @classmethod
  def format_members(cls, o, colorize=False):
    s = []
    items = []
    longest_k = 0
    types = {}
    type_i = 0
    color = 0
    
    for k in dir(o):
      v = getattr(o,k)
      if len(k) > longest_k:
        longest_k = len(k)
      if colorize:
        t = str(type(v))
        if t not in types:
          types[t] = type_i
          type_i += 1
        color = 31 + (types[t] % 5)
      items.append((k,v,color))
    
    if colorize:
      pat = '\033[1;%%dm%%-%ds\033[m = \033[1;%%dm%%s\033[m' % longest_k
    else:
      pat = '%%-%ds = %%s' % longest_k
    
    for k,v,color in items:
      v = cls._repr.repr(v)
      if colorize:
        s.append(pat % (color, k, color, v))
      else:
        s.append(pat % (k, v))
    
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
    
    if info is None:
      return None
    
    va_kwa_wrapper = None
    
    if not info['varargs'] and not info['varkw']:
      def va_kwa_wrapper(*args, **kwargs):
        return f(*args[:len(info['args'])])
    elif not info['varargs']:
      def va_kwa_wrapper(*args, **kwargs):
        return f(*args[:len(info['args'])], **kwargs)
    elif not info['varkw']:
      def va_kwa_wrapper(*args, **kwargs):
        return f(*args)
    
    if va_kwa_wrapper:
      va_kwa_wrapper.info = frozendict(info.update({
        'varargs': True,
        'varkw': True
      }))
      cls._info_cache[callable_cache_key(f)] = va_kwa_wrapper.info
      va_kwa_wrapper.wrapped_func = f
      va_kwa_wrapper.im_func = f
      try:
        va_kwa_wrapper.im_class = f.im_class
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


class UTCTimeZone(tzinfo):
  '''UTC
  '''
  def __new__(cls):
    try:
      return cls._instance
    except AttributeError:
      cls._instance = tzinfo.__new__(UTCTimeZone)
    return cls._instance
  
  def utcoffset(self, dt):
    return ZERO_TIMEDELTA
  
  def tzname(self, dt):
    return "UTC"
  
  def dst(self, dt):
    return ZERO_TIMEDELTA
  
  def __repr__(self):
    return 'UTCTimeZone()'
  

class TimeZone(tzinfo):
  '''Fixed offset in minutes east from UTC.
  '''
  def __init__(self, tzstr_or_minutes):
    if isinstance(tzstr_or_minutes, basestring):
      minutes = (int(tzstr_or_minutes[1:3]) * 60) + int(tzstr_or_minutes[4:6])
      if tzstr_or_minutes[0] == '-':
        minutes = -minutes
    else:
      minutes = tzstr_or_minutes
    self.__minute_offset = minutes
    self.__offset = timedelta(minutes=minutes)
  
  def utcoffset(self, dt):
    return self.__offset
  
  def dst(self, dt):
    return ZERO_TIMEDELTA
  
  def __repr__(self):
    return 'TimeZone(%d)' % self.__minute_offset
  

class DateTime(datetime):
  '''Time zone aware version of datetime with additional parsers.
  '''
  XML_SCHEMA_DATETIME_RE = re.compile(r'((?#year)-?\d{4})-((?#month)\d{2})-((?#day)\d{2})T'\
    r'((?#hour)\d{2}):((?#minute)\d{2}):((?#second)\d{2})((?#millis)\.\d+|)((?#tz)[+-]\d{2}:\d{2}|Z?)')
  '''XML schema dateTime regexp.
  
  :type: RegexType
  '''
  def __new__(cls, dt=None, *args, **kwargs):
    if isinstance(dt, datetime):
      if isinstance(dt, cls):
        return dt
      return datetime.__new__(cls, 
        dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond, dt.tzinfo)
    return datetime.__new__(cls, dt, *args, **kwargs)
  
  def as_utc(self):
    '''Return this date in Universal Time Coordinate
    '''
    if self.tzinfo is UTCTimeZone():
      return self
    dt = (self - self.utcoffset()).replace(tzinfo=UTCTimeZone())
    return DateTime(dt)
  
  @classmethod
  def now(self):
    if time.timezone == 0 and time.daylight == 0:
      tz = UTCTimeZone()
    else:
      tz = TimeZone(((-time.timezone)/60) + (time.daylight * 60))
    return datetime.now().replace(tzinfo=tz)
  
  @classmethod
  def parse_xml_schema_dateTime(cls, string):
    '''Parse a XML Schema dateTime value.
    
    :see: `XML Schema Part 2: Datatypes Second Edition, 3.2.7 dateTime
          <http://www.w3.org/TR/xmlschema-2/#dateTime>`__
    '''
    m = cls.XML_SCHEMA_DATETIME_RE.match(string).groups()
    if m[7] and m[7] != 'Z':
      tz = TimeZone(m[7])
    else:
      tz = UTCTimeZone()
    microsecond = 0
    if m[6]:
      microsecond = int(float(m[6]) * 1000000.0)
    dt = DateTime(int(m[0]), int(m[1]), int(m[2]), int(m[3]), int(m[4]), int(m[5]), microsecond, tz)
    return dt
  


def callable_cache_key(node):
  '''Calculate key unique enought to be used for caching callables.
  '''
  if not isinstance(node, (MethodType, FunctionType)):
    return hash(node.__call__)^hash(node)
  elif isinstance(node, MethodType):
    return hash(node)^hash(node.im_class)
  return node



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

def load_modules(path, deep=False, skip_first_init=True):
  '''Import all modules in a directory.
  
  :param path: Path of a directory
  :type  path: string
  :param deep: Search subdirectories
  :type  deep: bool
  :param skip_first_init: Do not load any __init__ directly under `path`.
                          Note that if `deep` is ``True``, 
                          subdirectory/__init__ will still be loaded, 
                          even if `skip_first_init` is ``True``.
  :type  skip_first_init: bool
  :returns: A dictionary of modules imported, keyed by name.
  :rtype:   dict'''
  loaded = {}
  _load_modules(path, deep, skip_first_init, '', loaded)
  return loaded

def _load_modules(path, deep, skip_init, parent_name, loaded):
  seen = []
  
  for f in os.listdir(path):
    fpath = os.path.join(path, f)
    
    if os.path.isdir(fpath):
      if deep:
        _load_modules(fpath, deep, False, f, loaded)
      else:
        continue
    
    name = strip_filename_extension(f)
    
    if skip_init and name == '__init__':
      continue
    
    if f[0] != '.' and f[-3:] in ('.py', 'pyc') and name not in seen:
      fp, pathname, desc = imp.find_module(name, [path])
      m = None
      try:
        sys.path.append(path)
        m = imp.load_module(name, fp, pathname, desc)
        abs_name = name
        if parent_name:
          if name == '__init__':
            abs_name = parent_name
          else:
            abs_name = '%s.%s' % (parent_name, name)
        elif name == '__init__':
          # in the case where skip_first_init is False
          abs_name = os.path.basename(path)
        loaded[abs_name] = m
      finally:
        if fp:
          fp.close()
      
      seen.append(name)
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
