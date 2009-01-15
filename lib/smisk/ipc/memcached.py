# encoding: utf-8
try:
  import cmemcached as memcache
except ImportError:
  try:
    import memcache
  except ImportError:
    raise ImportError('neither cmemcached nor memcache module is available')

from smisk.util.cache import app_shared_key
from smisk.util.type import MutableMapping
from smisk.core import object_hash

_dicts = {}

def shared_dict(name=None, nodes=['127.0.0.1:11211'], memcached_debug=0):
  '''Shared memcached-based dictionary.
  '''
  if name is None:
    name = app_shared_key()
  dicts_ck = name + object_hash(nodes)
  try:
    return _dicts[dicts_ck]
  except KeyError:
    pass
  client = memcache.Client(nodes, debug=memcached_debug)
  d = MCDict(client, name)
  _dicts[dicts_ck] = d
  return d


class MCDict(dict, MutableMapping):
  def __init__(self, client, key_prefix=None):
    self.client = client
    self.key_prefix = key_prefix
  
  def __getitem__(self, key):
    if self.key_prefix:
      key = self.key_prefix + key
    obj = self.client.get(key)
    if obj is None:
      raise KeyError(key)
    return obj
  
  def __contains__(self, key):
    if self.key_prefix:
      key = self.key_prefix + key
    if self.client.get(key):
      return True
    return False
  
  def __setitem__(self, key, value):
    if self.key_prefix:
      key = self.key_prefix + key
    self.client.set(key, value)
  
  def __delitem__(self, key):
    if self.key_prefix:
      key = self.key_prefix + key
    self.client.delete(key)
  
  def __len__(self): raise NotImplementedError('__len__')
  def __iter__(self): raise NotImplementedError('__iter__')
  def keys(self): raise NotImplementedError('keys')
  def items(self): raise NotImplementedError('items')
  def iteritems(self): raise NotImplementedError('iteritems')
  def values(self): raise NotImplementedError('values')
  
  def __repr__(self):
    return '<%s.%s @ 0x%x %s>' % (
      self.__module__, self.__class__.__name__, id(self), self.client)
  
