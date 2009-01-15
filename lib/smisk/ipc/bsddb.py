#!/bin/env python
#------------------------------------------------------------------------
#       Copyright (c) 1997-2001 by Total Control Software
#             All Rights Reserved
#------------------------------------------------------------------------
#
# Module Name:  dbShelve.py
#
# Description:  A reimplementation of the standard shelve.py that
#               forces the use of cPickle, and DB.
#
# Creation Date:  11/3/97 3:39:04PM
#
# License:    This is free software.  You may use this software for any
#             purpose including modification/redistribution, so long as
#             this header remains intact and that you do not claim any
#             rights of ownership or authorship of this software.  This
#             software has been tested, but no warranty is expressed or
#             implied.
#
# 13-Dec-2000:  Updated to be used with the new bsddb3 package.
#               Added DBDictCursor class.
#
# Modified by Rasmus Andersson for the Smisk project.
#
#------------------------------------------------------------------------

"""Manage shelves of pickled objects using bsddb database files for the
storage.
"""

#------------------------------------------------------------------------

import cPickle
import sys, os, atexit
import smisk.core.bsddb as db
from smisk.util.cache import app_shared_key
from smisk.util.type import MutableMapping
from tempfile import gettempdir

#At version 2.3 cPickle switched to using protocol instead of bin
if sys.version_info[:3] >= (2, 3, 0):
  HIGHEST_PROTOCOL = cPickle.HIGHEST_PROTOCOL
# In python 2.3.*, "cPickle.dumps" accepts no
# named parameters. "pickle.dumps" accepts them,
# so this seems a bug.
  if sys.version_info[:3] < (2, 4, 0):
    def _dumps(object, protocol):
      return cPickle.dumps(object, protocol)
  else :
    def _dumps(object, protocol):
      return cPickle.dumps(object, protocol=protocol)

else:
  HIGHEST_PROTOCOL = None
  def _dumps(object, protocol):
    return cPickle.dumps(object, bin=protocol)



#------------------------------------------------------------------------

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
  
  if not os.path.isdir(homedir):
    os.mkdir(homedir)
  
  if not dbenv:
    dbenv = db.DBEnv(0)
    dbenv.open(homedir, db.DB_CREATE | db.DB_INIT_MPOOL | db.DB_INIT_CDB, 0)
  
  d = DBDict(dbenv, sync=persistent)
  d.open(filename, name, type, flags, mode)
  _dicts[filename] = d
  
  if not persistent and is_tempdir:
    import shutil
    atexit.register(shutil.rmtree, homedir, True)
  
  return d

#---------------------------------------------------------------------------

class DBDictError(db.DBError): pass


class DBDict(dict, MutableMapping):
  """Hold pickled objects, built upon a bsddb DB object.  It
  automatically pickles/unpickles data objects going to/from the DB.
  """
  
  def __init__(self, dbenv=None, sync=False):
    self.db = db.DB(dbenv)
    self.sync = sync
    self._closed = True
    if HIGHEST_PROTOCOL:
      self.protocol = HIGHEST_PROTOCOL
    else:
      self.protocol = 1


  def __del__(self):
    self.close()


  def __getattr__(self, name):
    """Many methods we can just pass through to the DB object.
    (See below)
    """
    return getattr(self.db, name)


  #-----------------------------------
  # Dictionary access methods

  def __len__(self):
    return len(self.db)


  def __getitem__(self, key):
    return cPickle.loads(self.db[key])
  
  def __setitem__(self, key, value):
    self.db[key] = _dumps(value, self.protocol)
  
  def __delitem__(self, key):
    del self.db[key]
  
  def __contains__(self, key):
    return self.db.has_key(key)
  
  if sys.version_info[0:2] >= (2, 6):
    def __iter__(self):
      return self.db.__iter__()
  else:
    def __iter__(self):
      return iter(self.db.items())
  
  def open(self, *args, **kwargs):
    self.db.open(*args, **kwargs)
    self._closed = False


  def close(self, *args, **kwargs):
    if self.sync:
      self.db.sync()
    self.db.close(*args, **kwargs)
    self._closed = True
  
  def __repr__(self):
    if self._closed:
      return '<%s.%s @ 0x%x - closed>' % (
        self.__module__, self.__class__.__name__, id(self), items)
    else:
      return repr(dict([(k, cPickle.loads(v)) for k,v in self.db.items()]))
  
  def keys(self, txn=None):
    if txn != None:
      return self.db.keys(txn)
    else:
      return self.db.keys()

  def values(self, txn=None):
    if txn != None:
      values = self.db.values(txn)
    else:
      values = self.db.values()
    return [cPickle.loads(v) for v in values]
  
  def items(self, txn=None):
    if txn != None:
      items = self.db.items(txn)
    else:
      items = self.db.items()
    return [(k, cPickle.loads(v)) for k,v in items]

  #-----------------------------------
  # Other methods

  def __append(self, value, txn=None):
    data = _dumps(value, self.protocol)
    return self.db.append(data, txn)

  def append(self, value, txn=None):
    if self.get_type() == db.DB_RECNO:
      return self.__append(value, txn=txn)
    raise DBDictError, "append() only supported when opened with filetype=DB_RECNO"


  def associate(self, secondaryDB, callback, flags=0):
    def _dbdict_associate_callback(priKey, priData, realCallback=callback):
      # Safe in Python 2.x because expresion short circuit
      if sys.version_info[0] < 3 or isinstance(priData, bytes) :
        data = cPickle.loads(priData)
      else :
        data = cPickle.loads(bytes(priData, "iso8859-1"))  # 8 bits
      return realCallback(priKey, data)

    return self.db.associate(secondaryDB, _dbdict_associate_callback, flags)


  #def get(self, key, default=None, txn=None, flags=0):
  def get(self, *args, **kw):
    # We do it with *args and **kw so if the default value wasn't
    # given nothing is passed to the extension module.  That way
    # an exception can be raised if set_get_returns_none is turned
    # off.
    data = self.db.get(*args, **kw)
    try:
      return cPickle.loads(data)
    except (EOFError, TypeError, cPickle.UnpicklingError):
      return data  # we may be getting the default value, or None,
             # so it doesn't need unpickled.

  def get_both(self, key, value, txn=None, flags=0):
    data = _dumps(value, self.protocol)
    data = self.db.get(key, data, txn, flags)
    return cPickle.loads(data)


  def cursor(self, txn=None, flags=0):
    c = DBDictCursor(self.db.cursor(txn, flags))
    c.protocol = self.protocol
    return c


  def put(self, key, value, txn=None, flags=0):
    data = _dumps(value, self.protocol)
    return self.db.put(key, data, txn, flags)


  def join(self, cursorList, flags=0):
    raise NotImplementedError


  #----------------------------------------------
  # Methods allowed to pass-through to self.db
  #
  #  close,  delete, fd, get_byteswapped, get_type, has_key,
  #  key_range, open, remove, rename, stat, sync,
  #  upgrade, verify, and all set_* methods.


#---------------------------------------------------------------------------

class DBDictCursor:
  """
  """
  def __init__(self, cursor):
    self.dbc = cursor

  def __del__(self):
    self.close()


  def __getattr__(self, name):
    """Some methods we can just pass through to the cursor object.  (See below)"""
    return getattr(self.dbc, name)


  #----------------------------------------------

  def dup(self, flags=0):
    c = DBDictCursor(self.dbc.dup(flags))
    c.protocol = self.protocol
    return c


  def put(self, key, value, flags=0):
    data = _dumps(value, self.protocol)
    return self.dbc.put(key, data, flags)


  def get(self, *args):
    count = len(args)  # a method overloading hack
    method = getattr(self, 'get_%d' % count)
    apply(method, args)

  def get_1(self, flags):
    rec = self.dbc.get(flags)
    return self._extract(rec)

  def get_2(self, key, flags):
    rec = self.dbc.get(key, flags)
    return self._extract(rec)

  def get_3(self, key, value, flags):
    data = _dumps(value, self.protocol)
    rec = self.dbc.get(key, flags)
    return self._extract(rec)


  def current(self, flags=0): return self.get_1(flags|db.DB_CURRENT)
  def first(self, flags=0): return self.get_1(flags|db.DB_FIRST)
  def last(self, flags=0): return self.get_1(flags|db.DB_LAST)
  def next(self, flags=0): return self.get_1(flags|db.DB_NEXT)
  def prev(self, flags=0): return self.get_1(flags|db.DB_PREV)
  def consume(self, flags=0): return self.get_1(flags|db.DB_CONSUME)
  def next_dup(self, flags=0): return self.get_1(flags|db.DB_NEXT_DUP)
  def next_nodup(self, flags=0): return self.get_1(flags|db.DB_NEXT_NODUP)
  def prev_nodup(self, flags=0): return self.get_1(flags|db.DB_PREV_NODUP)


  def get_both(self, key, value, flags=0):
    data = _dumps(value, self.protocol)
    rec = self.dbc.get_both(key, flags)
    return self._extract(rec)


  def set(self, key, flags=0):
    rec = self.dbc.set(key, flags)
    return self._extract(rec)

  def set_range(self, key, flags=0):
    rec = self.dbc.set_range(key, flags)
    return self._extract(rec)

  def set_recno(self, recno, flags=0):
    rec = self.dbc.set_recno(recno, flags)
    return self._extract(rec)

  set_both = get_both

  def _extract(self, rec):
    if rec is None:
      return None
    else:
      key, data = rec
      # Safe in Python 2.x because expresion short circuit
      if sys.version_info[0] < 3 or isinstance(data, bytes) :
        return key, cPickle.loads(data)
      else :
        return key, cPickle.loads(bytes(data, "iso8859-1"))  # 8 bits

  #----------------------------------------------
  # Methods allowed to pass-through to self.dbc
  #
  # close, count, delete, get_recno, join_item

