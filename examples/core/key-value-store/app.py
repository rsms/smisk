#!/usr/bin/env python
# encoding: utf-8
import os
from smisk.core import Application
from smisk.ipc import shared_dict
from smisk.serialization.json import json_encode, json_decode

class KeyValueStore(Application):
  '''A very simple key-value store using shared memory
  '''
  
  def __init__(self, *va, **kw):
    '''Setup the application
    '''
    Application.__init__(self, *va, **kw)
    
    # Use a shared dict, mapped in shared memory and shared between processes
    self.entries = shared_dict(homedir=os.path.join(os.path.dirname(__file__), 'store'),
      persistent=True)
  
  
  def service(self):
    '''Handle a request
    '''
    # The key is the request path
    key = self.request.url.path.strip('/')
    
    # Set content-type
    self.response.headers = ['Content-Type: application/json']
    
    # Standard reply
    rsp = '{"status": "OK"}'
    
    if not key:
      # Empty key means list all avilable keys
      if self.request.method == 'GET':
        rsp = json_encode({'keys': self.entries.keys()})
      else:
        rsp = self.method_not_allowed()
    else:
      # Non-empty key means manipulate the store
      # HTTP method defines the action
      if self.request.method == 'GET':
        # Read an entry
        try:
          rsp = json_encode(self.entries[key])
        except KeyError:
          rsp = self.not_found(key)
      elif self.request.method in ('PUT', 'POST'):
        # Set an antry
        self.entries[key] = json_decode(self.request.input.read(1024*1024))
      elif self.request.method == 'DELETE':
        # Delete an entry
        try:
          del self.entries[key]
        except KeyError:
          rsp = self.not_found(key)
      else:
        rsp = self.method_not_allowed()
    
    # Respond
    self.response.headers.append('Content-Length: %d' % (len(rsp)+1) )
    self.response(rsp, '\n')
  
  
  def not_found(self, key):
    '''Create a 404 Not Found response
    '''
    self.response.headers.append('Status: 404 Not Found')
    return '{"status": "No such key %r"}' % key
  
  
  def method_not_allowed(self):
    '''Create a 405 Method Not Allowed response
    '''
    self.response.headers.append('Status: 405 Method Not Allowed')
    return '{"status": "Method Not Allowed"}'

try:
  KeyValueStore().run()
except KeyboardInterrupt:
  pass
