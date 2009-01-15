#!/usr/bin/env python
# encoding: utf-8
from smisk.mvc import *
from smisk.ipc import shared_dict
from smisk.config import config

class root(Controller):
  def __init__(self):
    # If persistent evaluates to True, the contents of the shared 
    # dict will be flushed to disk on shutdown and read from disk 
    # on startup, thus providing a persistent set of data.
    self.entries = shared_dict(persistent=config.get('persistent'))
  
  @expose(methods='GET')
  def __call__(self):
    '''List available entries.
    '''
    return {'entries': self.entries}
  
  @expose(methods=('POST', 'PUT'))
  def set(self, key, value):
    '''Create or modify an entry.
    '''
    self.entries[key] = value
  
  @expose(methods='GET')
  def get(self, key):
    '''Get value for key.
    '''
    try:
      return {'value': self.entries[key]}
    except KeyError:
      raise http.NotFound('no value associated with key %r' % key)
  
  @expose(methods='DELETE')
  def delete(self, key):
    '''Remove entry.
    '''
    if key not in self.entries:
      raise http.NotFound('no such entry %r' % key)
    del self.entries[key]
  

if __name__ == '__main__':
  # Load the configuration file key-value-store.conf while assembling
  # the application
  main(config='key-value-store')
