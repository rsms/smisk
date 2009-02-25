# encoding: utf-8
import logging
import sys, os, atexit, shutil
import smisk.core.bsddb as db
from smisk.util.cache import app_shared_key
from datetime import datetime

log = logging.getLogger(__name__)
dbenvs = {}

class BSDDBTable(object):
  def __init__(self, envpath, name=None, version=None):
    self._closed = True
    self.version = version
    
    # Save parameters
    self.envpath = os.path.abspath(envpath)
    if name is None:
      name = app_shared_key()
    self.name = name
    
    # Make sure we have a env directory
    if not os.path.isdir(self.envpath):
      if os.path.exists(self.envpath):
        log.debug('removing non-directory envpath %r', self.envpath)
        os.remove(self.envpath)
      log.debug('creating envpath directory at %r', self.envpath)
      os.mkdir(self.envpath)
    
    # Aquire DB env
    global dbenvs
    try:
      dbenv = dbenvs[self.envpath]
    except KeyError:
      dbenv = db.DBEnv(0)
      dbenv.open(self.envpath, db.DB_CREATE | db.DB_INIT_MPOOL | db.DB_INIT_CDB, 0)
      dbenvs[self.envpath] = dbenv
    
    # Setup and open
    self.db = db.DB(dbenv)
    self.db.open(os.path.join(self.envpath, self.name), self.name, db.DB_BTREE, db.DB_CREATE, 0600)
    self._closed = False
  
  def __del__(self):
    self.close()
  
  def close(self, *args, **kwargs):
    if not self._closed:
      self.db.sync()
      self.db.close(*args, **kwargs)
      self._closed = True
  
  # Basic manipulation
  
  def mkkey(self, key, column, version):
    return '%s-%s-%s' % (key, column, version.strftime('%Y%m%d%H%M%S'))
  
  def set_column(self, key, column, data, version=None):
    if version is None:
      version = self.version
    self.db.put(self.mkkey(key, column, version), data)
  
  def get_column(self, key, column, version=None):
    if version is None:
      version = self.version
    return self.db[self.mkkey(key, column, version)]
  
  def delete_column(self, key, column, version=None):
    if version is None:
      version = self.version
    del self.db[self.mkkey(key, column, version)]
  
  # Convenience methods
  
  def set_columns(self, key, columns_values, version=None):
    for column, value in columns_values.items():
      self.set_column(key, column, value, version)
  
  def get_columns(self, key, columns, version=None):
    columns_values = {}
    for column in columns:
      columns_values[column] = self.get_column(key, column, version)
    return columns_values
  


def mktemp_envpath():
  from tempfile import gettempdir
  import atexit, shutil
  envpath = os.path.join(gettempdir(), app_shared_key())
  try:
    shutil.rmtree(envpath, True)
    os.mkdir(envpath)
  except:
    pass
  atexit.register(shutil.rmtree, envpath, True)
  return envpath


if __name__ == '__main__':
  envpath = mktemp_envpath()
  t = BSDDBTable(envpath, version=datetime.now())
  
  # Basic tests
  if 0:
    t.set_column('rasmus', 'name', 'Rasmus Andersson')
    t.set_column('rasmus', 'age', '25')
    t.set_columns('john', {'name':'John Doe', 'age':'32'})
    assert t.get_column('rasmus', 'age') == '25'
    row = t.get_columns('rasmus', ('name','age'))
    assert row['name'] == 'Rasmus Andersson'
    assert row['age'] == '25'
  
  # 2
  import random
  from datetime import timedelta
  
  num_records = 4
  columns = ['name', 'age', 'password']
  num_versions = len(columns)
  
  keys = []
  for x in range(num_records):
    keys.append('key%d' % x)
  
  versions = []
  for x in range(num_versions):
    versions.append(datetime.now() + timedelta(x, x))
  
  # Write randomly
  print 'The data viewed in a logical table structure'
  print '--------------------------------------------\n'
  divrow = '+---------------------+---------------------+---------------------+---------------------+---------------------+'
  for version_i, version in enumerate(versions):
    cols = []
    for i,column in enumerate(columns):
      if i == version_i:
        column += '_v%d' % (version_i+1)
      cols.append(column)
    
    print '+-------------------------------------------------------------------------------------------------------------+'
    print '|                                Version %14s                                                       |' % version.strftime('%Y%m%d%H%M%S')
    print divrow
    print '| %-19s | %-19s | %-19s | %-19s | %-19s |' % tuple(['Primary key', 'Version'] + cols)
    print divrow.replace('-','=')
    for key in random.sample(keys, num_records):
      #key = key_samples[(x+1) % len(keys)]
      #key = keys[random.randint(0, num_records-1)]
      sys.stdout.write('| %-19s | %-19s ' % (key, version.strftime('%Y%m%d%H%M%S')))
      #for column in random.sample(columns, len(columns)):
      for column in cols:
        value = 'v%s%s%d' % (key, column, x)
        sys.stdout.write('| %-19s ' % value)
        t.set_column(key, column, value, version)
      sys.stdout.write('|\n')
      print divrow
    print ''
  
  # Iterate sequential
  print 'How data is stored'
  print '------------------\n'
  divrow = '+-----------------------------------+-----------------------------------+'
  print divrow
  print '| %-33s | %-33s |' % ('Key', 'Value')
  print divrow.replace('-','=')
  for k,v in t.db.items():
    print '| %-33s | %-33s |' % (k, v)
    print divrow
