#!/usr/bin/env python
# encoding: utf-8
from smisk.mvc import *
from smisk.ipc.bsddb import shared_dict
from smisk.config import config

class root(Controller):
  def __init__(self):
    # If persistent evaluates to True, the contents of the shared 
    # dict will be flushed to disk on shutdown and read from disk 
    # on startup, thus providing a persistent set of data.
    self.entries = shared_dict(persistent=config.get('persistent'))
  
  def __call__(self):
    pass
  
  @expose(methods='GET')
  def entry(self):
    '''List available keys.
    '''
    return {'keys': self.entries.keys()}
  
  @expose(methods=('POST', 'PUT'))
  def set(self, key, value):
    '''Create or modify an entry.
    '''
    self.entries[key.encode('utf-8')] = value
  
  @expose(methods='GET')
  def get(self, key):
    '''Get value for key.
    '''
    try:
      return {'value': self.entries[key.encode('utf-8')]}
    except KeyError:
      raise http.NotFound('no value associated with key %r' % key)
  
  @expose(methods='DELETE')
  def delete(self, key):
    '''Remove entry.
    '''
    utf8_key = key.encode('utf-8')
    if utf8_key not in self.entries:
      raise http.NotFound(u'no such entry %r' % key)
    del self.entries[utf8_key]
  

if __name__ == '__main__':
  # Load the configuration file key-value-store.conf while assembling
  # the application
  main(config='key-value-store')
