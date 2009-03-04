# encoding: utf-8
import os, atexit, shutil
from smisk.util._bsddb import db, dbshelve
from smisk.util.cache import app_shared_key
from tempfile import gettempdir

_dicts = {}

def shared_dict(filename=None, homedir=None, name=None, mode=0600, dbenv=None, 
                type=db.DB_HASH, flags=db.DB_CREATE, persistent=False):
  orig_name = name
  is_tempdir = False
  
  if filename:
    filename = os.path.abspath(filename)
    homedir = os.path.dirname(filename)
    name = os.path.basename(filename)
  else:
    if name is None:
      name = app_shared_key()
    if homedir is None:
      is_tempdir = True
      homedir = os.path.join(gettempdir(), '%s.ipc' % name)
    filename = os.path.join(homedir, name)
  
  try:
    return _dicts[filename]
  except KeyError:
    pass
  
  if not persistent and os.path.isdir(homedir):
    try:
      shutil.rmtree(homedir, True)
      os.mkdir(homedir)
    except:
      pass
  
  if not os.path.isdir(homedir):
    if os.path.exists(homedir):
      os.remove(homedir)
    os.mkdir(homedir)
  
  if not dbenv:
    dbenv = db.DBEnv(0)
    dbenv.open(homedir, db.DB_CREATE | db.DB_INIT_MPOOL | db.DB_INIT_CDB, 0)
  
  d = DBDict(dbenv, sync=persistent)
  d.open(filename, name, type, flags, mode)
  _dicts[filename] = d
  
  if not persistent and is_tempdir:
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
  
  def close(self, *args, **kwargs):
    try:
      if self.sync:
        self.db.sync()
      self.db.close(*args, **kwargs)
    except db.DBError:
      pass
    self._closed = True
  
