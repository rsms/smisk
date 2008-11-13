# encoding: utf-8
'''Python utilities, like finding and loading modules
'''
import sys, os, imp
from smisk.util.collections import unique_wild
from smisk.util.string import strip_filename_extension
from smisk.util.type import None2

__all__ = ['format_exc', 'wrap_exc_in_callable', 'classmethods', 'unique_sorted_modules_of_items', 'list_python_filenames_in_dir', 'find_modules_for_classtree', 'load_modules']

def format_exc(exc=None, as_string=False):
  ''':rtype: string
  '''
  if exc is None:
    exc = sys.exc_info()
  if exc == (None, None, None):
    return ''
  import traceback
  if as_string:
    return ''.join(traceback.format_exception(*exc))
  else:
    return traceback.format_exception(*exc)


def wrap_exc_in_callable(exc):
  '''Wrap exc in a anonymous function, for later raising.
  
  :rtype: callable
  '''
  def exc_wrapper(*args, **kwargs):
    raise exc
  return exc_wrapper


def classmethods(cls):
  '''List names of all class methods in class `cls`.
  
  :rtype: list
  '''
  return [k for k in dir(cls) \
    if (k[0] != '_' and getattr(getattr(cls, k), 'im_class', None) == type)]


def unique_sorted_modules_of_items(v):
  ''':rtype: list
  '''
  s = []
  for t in v:
    s.append(t.__module__)
  s = unique_wild(s)
  s.sort()
  return s


def list_python_filenames_in_dir(path, only_py=True):
  ''':rtype: list
  '''
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
      names = unique_wild(names)
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


def find_closest_syspath(path, namebuf):
  '''TODO
  '''
  namebuf.append(os.path.basename(path))
  if path in sys.path:
    del namebuf[-1]
    return '.'.join(reversed(namebuf)), path
  path = os.path.dirname(path)
  if not path or len(path) == 1:
    return None2
  return find_closest_syspath(path, namebuf)


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
  path = os.path.abspath(path)
  parent_name, top_path = find_closest_syspath(path, [])
  sys.path[0:0] = [top_path]
  try:
    _load_modules(path, deep, skip_first_init, parent_name, loaded)
  finally:
    if sys.path[0] == top_path:
      sys.path = sys.path[1:]
  return loaded

def _load_modules(path, deep, skip_init, parent_name, loaded):
  for f in os.listdir(path):
    fpath = os.path.join(path, f)
  
    if os.path.isdir(fpath):
      if deep:
        # skip_init is False because this method is a slave and the
        # master argument is skip_first_init.
        _load_modules(fpath, deep, False, f, loaded)
      continue
  
    name = strip_filename_extension(f)
    if skip_init and name == '__init__':
      continue
    if parent_name:
      if name == '__init__':
        name = parent_name
      else:
        name = '%s.%s' % (parent_name, name)
    elif name == '__init__':
      # in the case where skip_init is False
      name = os.path.basename(path)
    
    if name not in loaded:
      mfindpath = list(sys.path)
      mod = None
      components = name.split('.')
      org_sys_path = list(sys.path)
      try:
        for comp in components:
          mfile, mpath, mdesc = imp.find_module(comp, sys.path)
          if mdesc[0] == '':
            mfindpath = mpath
          else:
            mfindpath = os.path.dirname(mpath)
          sys.path[0:0] = [mfindpath]
          mod = imp.load_module(comp, mfile, mpath, mdesc)
        if mod is not None:
          loaded[name] = mod
      finally:
        sys.path = org_sys_path
  return loaded
