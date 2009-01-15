#!/usr/bin/env python
# encoding: utf-8
from smisk.mvc import *
from smisk.mvc.model import *
from smisk.ipc import shared_dict
from smisk.config import config

class root(Controller):
  def __init__(self):
    self.entries = shared_dict(persistent=config.get('persistent'))
  
  @expose(methods='GET')
  def __call__(self):
    '''Lists all available keys.
    '''
    return {'pid': os.getpid(), 'entries': self.entries}
  
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
      return {'pid': os.getpid(), 'value': self.entries[key]}
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
  main(config='key-value-store')
