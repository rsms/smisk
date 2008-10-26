# encoding: utf-8
# This module is based on paste.registry (c) 2005 Ben Bangert, released under
# the MIT license.
'''Object proxy
'''

class ObjectProxy(object):
  '''Proxy an arbitrary object, making it possible to change values that are
  passed around.
  '''
  def __new__(cls, obj=None):
    '''Create a new ObjectProxy
    '''
    self = object.__new__(cls)
    self.__dict__['__object__'] = obj
    return self
  
  def _object(self):
    return self.__dict__['__object__']
  
  def _set_object(self, obj):
    self.__dict__['__object__'] = obj
  
  def __getattr__(self, attr):
    return getattr(self._object(), attr)
  
  def __setattr__(self, attr, value):
    setattr(self._object(), attr, value)
  
  def __delattr__(self, name):
    delattr(self._object(), name)
  
  def __getitem__(self, key):
    return self._object()[key]
  
  def __setitem__(self, key, value):
    self._object()[key] = value
  
  def __delitem__(self, key):
    del self._object()[key]
  
  def __call__(self, *args, **kw):
    return self._object()(*args, **kw)
  
  def __repr__(self):
    try:
      return repr(self._object())
    except (TypeError, AttributeError):
      return '<%s.%s object at 0x%x>' %\
        (self.__class__.__module__, self.__class__.__name__, id(self))
  
  def __iter__(self):
    return iter(self._object())
  
  def __len__(self):
    return len(self._object())
  
  def __contains__(self, key):
    return key in self._object()
  
  def __hash__(self):
    return hash(self._object())
  
  def __nonzero__(self):
    return bool(self._object())
  
  def __eq__(self, b):
    return self._object() == b
  
  def __cmp__(self, b):
    return cmp(self._object(), b)
  
