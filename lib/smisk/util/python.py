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


def load_modules(path, deep=False, skip_first_init=True, libdir=None, parent_name=None):
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
  loaded = sys.modules.copy()
  path = os.path.abspath(path)
  if libdir and parent_name:
    top_path = os.path.abspath(libdir)
    parent_name = parent_name
  else:
    parent_name, top_path = find_closest_syspath(path, [])
  sys.path[0:0] = [top_path]
  loaded_paths = {}
  for name,mod in sys.modules.items():
    if mod:
      try:
        loaded_paths[strip_filename_extension(mod.__file__)] = mod
      except AttributeError:
        pass
  try:
    _load_modules(path, deep, skip_first_init, parent_name, loaded, loaded_paths)
  finally:
    if sys.path[0] == top_path:
      sys.path = sys.path[1:]
  return loaded

def _load_modules(path, deep, skip_init, parent_name, loaded, loaded_paths):
  for f in os.listdir(path):
    fpath = os.path.join(path, f)
    
    if strip_filename_extension(fpath) in loaded_paths:
      #print >> sys.stderr, 'AVOIDED reloading '+fpath
      continue
    
    if os.path.isdir(fpath):
      if deep and ( os.path.isfile(os.path.join(fpath, '__init__.py')) 
                    or os.path.isfile(os.path.join(fpath, '__init__.pyc'))
                    or os.path.isfile(os.path.join(fpath, '__init__.pyo')) ):
          # skip_init is False because this method is a slave and the
          # master argument is skip_first_init.
          if parent_name:
            parent_name = '%s.%s' % (parent_name, f)
          else:
            parent_name = f
          _load_modules(fpath, deep, False, parent_name, loaded, loaded_paths)
      continue
    
    if not os.path.splitext(f)[1].startswith('.py'):
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
      findpath = path
      mod = None
      load_namev = []
      load_name = ''
      namev = name.split('.')
      findpathv = findpath.strip('/').split('/')
      for i, name_part in enumerate(namev):
        load_namev.append(name_part)
        load_name = '.'.join(load_namev)
        
        findpathv_offset = len(namev)-i-1
        if findpathv_offset > 0:
          mfindpath = ['/'+os.path.join(*findpathv[:-findpathv_offset])]
          #print >> sys.stderr, 'A findpathv=%r, findpathv_offset=%r, mfindpath=%r' % (findpathv, findpathv_offset, mfindpath)
        else:
          mfindpath = ['/'+os.path.join(*findpathv)]
        
        try:
          mfile, mpath, mdesc = imp.find_module(name_part, mfindpath)
        except ImportError, e:
          #print >> sys.stderr, 'FAIL name_part=%r, mfindpath=%r' % (name_part, mfindpath)
          raise e
        
        if mfile is None:
          mpath += '/__init__.py'
        
        mpathn = strip_filename_extension(mpath)
        modn = loaded_paths.get(mpathn, None)
        
        if modn:
          mod = modn
          continue
        
        mod = imp.load_module(load_name, mfile, mpath, mdesc)
        loaded[load_name] = mod
        loaded_paths[strip_filename_extension(mpath)] = mod
      
      assert load_name == name
  
  return loaded
