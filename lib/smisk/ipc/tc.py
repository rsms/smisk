# encoding: utf-8
import os, atexit
import smisk.util._tc as tc
from smisk.util.cache import app_shared_key
from tempfile import gettempdir

_dicts = {}

def shared_dict(filename=None, type=tc.HDB, readonly=False, persistent=False, mode=0600):
  if not filename:
    name = app_shared_key()
    directory = os.path.join(gettempdir(), 'smisk.ipc.tc.%s' % name)
    if not os.path.isdir(directory):
      os.mkdir(directory, mode)
    filename = os.path.abspath(os.path.join(homedir, name))
  
  try:
    return _dicts[filename]
  except KeyError:
    pass
  
  flags = tc.HDBOWRITER | tc.HDBOCREAT
  if readonly:
    flags = tc.HDBOREADER  
  elif not persistent:
    flags |= tc.HDBOTRUNC
  
  d = type(filename, flags)
  
  if not persistent:
    atexit.register(os.remove, filename, True)
  
  _dicts[filename] = d
  return d

