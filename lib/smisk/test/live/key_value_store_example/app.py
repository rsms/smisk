#!/usr/bin/env python
# encoding: utf-8
from smisk.mvc import *
from smisk.mvc.model import *
from smisk.ipc.bsddb import shared_dict
from smisk.config import config

class root(Controller):
  def __init__(self):
    self.entries = shared_dict(persistent=False)
  
  @expose(methods='GET')
  def __call__(self):
    '''List available entries.
    '''
    response.headers.append('X-Pid: %d' % os.getpid())
    return {'entries': self.entries}
  
  @expose(methods=('POST', 'PUT'))
  def set(self, key, value):
    '''Create or modify an entry.
    '''
    response.headers.append('X-Pid: %d' % os.getpid())
    self.entries[key] = value
  
  @expose(methods='GET')
  def get(self, key):
    '''Get value for key.
    '''
    response.headers.append('X-Pid: %d' % os.getpid())
    try:
      return {'value': self.entries[key]}
    except KeyError:
      raise http.NotFound('no value associated with key %r' % key)
  
  @expose(methods='DELETE')
  def delete(self, key):
    '''Remove entry.
    '''
    response.headers.append('X-Pid: %d' % os.getpid())
    if key not in self.entries:
      raise http.NotFound('no such entry %r' % key)
    del self.entries[key]
  

if __name__ == '__main__':
  config.load(os.path.join(os.path.dirname(__file__), 'app.conf'))
  main()
