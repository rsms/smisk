# encoding: utf-8
import sys, os

class Singleton(object):
  def __new__(type):
    if not '_the_instance' in type.__dict__:
        type._the_instance = object.__new__(type)
    return type._the_instance

class Singleton2(object):
  """Singleton base class. Not thread safe."""
  def __new__(cls):
    raise Exception("singleton %s can not be instantiated" % cls.__name__)
  
  @classmethod
  def instance(cls):
    if not hasattr(cls, '_instance'):
      cls._instance = object.__new__(cls)
    return cls._instance
  

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
    names = list_unique_wild(names)
    names.sort()
  return names


def list_unique_wild(seq):
  # Not order preserving but faster than list_unique
  return list(set(seq))


def list_unique(seq, idfun=None):
  # Order preserving
  seen = set()
  return [x for x in seq if x not in seen and not seen.add(x)]


def format_exc(exc=None):
  '''
  :rtype string:
  '''
  if exc is None:
    exc = sys.exc_info()
  if exc == (None, None, None):
    return ''
  import traceback
  return ''.join(traceback.format_exception(*exc))
