#!/usr/bin/env python
# encoding: utf-8
from smisk.mvc import *
from smisk.mvc.model import *

class root(Controller):
  entries = {}
  
  @expose(methods='GET')
  def __call__(self):
    '''Lists all available keys.
    '''
    return {'keys': self.entries.keys()}
  
  @expose(methods=('POST', 'PUT'))
  def set(self, key, value):
    '''Creates an entry or modifies a value.
    '''
    self.entries[key] = value
  
  @expose(methods='GET')
  def get(self, key):
    '''Aquires a value.
    '''
    try:
      return {'value': self.entries[key]}
    except KeyError:
      raise http.NotFound('no value associated with key %r' % key)
  
  @expose(methods='DELETE')
  def delete(self, key):
    '''Removes an entry.
    '''
    if key not in self.entries:
      raise http.NotFound('no such entry %r' % key)
    del self.entries[key]
  

if __name__ == '__main__':
  main(config='method-based-kvs')
