# encoding: utf-8
import os, atexit, shutil
import smisk.util._tc as tc
from smisk.util.cache import app_shared_key
from tempfile import gettempdir

_dicts = {}

def shared_dict(filename=None, type=tc.HDB, readonly=False, persistent=False):
  is_tempdir = False
  
  if not filename:
    is_tempdir = True
    name = app_shared_key()
    directory = os.path.join(gettempdir(), '%s.ipc' % name)
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
  _dicts[filename] = d
  
  if not persistent:
    atexit.register(shutil.rmtree, homedir, True)
  
  return d


class DBDict(dbshelve.DBShelf):
  def __init__(self, dbenv, sync=False, *va, **kw):
    dbshelve.DBShelf.__init__(self, dbenv, *va, **kw)
    self.sync = sync
    self._closed = True
  
  def __del__(self):
    self.close()
    dbshelve.DBShelf.__del__(self)
  
  def open(self, *args, **kwargs):
    self.db.open(*args, **kwargs)
    self._closed = False
  
  def close(self, *args, **kwargs):
    try:
      if self.sync:
        self.db.sync()
      self.db.close(*args, **kwargs)
    except db.DBError:
      pass
    self._closed = True
  
