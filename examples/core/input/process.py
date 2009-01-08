#!/usr/bin/env python
# encoding: utf-8
import sys, os
from smisk.core import *

class MyApp(Application):
  def __init__(self, *args, **kwargs):
    super(MyApp, self).__init__(*args, **kwargs)
    # Set a very low session TTL for easy demonstration
    self.sessions.ttl = 10
    self.encoding = 'iso-8859-1'
  
  def service(self):
    self.response.headers = ["Content-Type: text/plain;charset=" + self.encoding]
    
    # Dump raw input?
    if 'dump' in self.request.get:
      while 1:
        chunk = self.request.input.read(8192)
        self.response.out.write(repr(chunk).strip("'").replace(r'\n', "\\n\n"))
        if len(chunk) < 8192:
          break
      return
    
    # Set a cookie
    if self.request.get.has_key('set_cookie'):
      self.response.set_cookie('a_cookie', self.request.get['set_cookie'], max_age=20)
    
    # Add some session data
    if self.request.get.has_key('set_session'):
      if self.request.get['set_session'] == '':
        self.request.session = None
      else:
        self.request.session = self.request.get['set_session']
    elif self.request.session is None:
      self.request.session = 'mos'
    
    # Reconstruct headers
    headers = []
    for k,v in self.request.env.items():
      if k.startswith('HTTP_'):
        headers.append('%s%s: %s' % (k[5],k[6:].lower(),v))
    
    # Print alot of information
    w = self.response.write
    w("self. %s\n" % repr(self))
    w(" request_class:       %s\n" % repr(self.request_class))
    w(" response_class       %s\n" % repr(self.response_class))
    w(" sessions_class: %s\n" % repr(self.sessions_class))
    w(" sessions.       %s\n" % repr(self.sessions))
    w("  name:                %s\n" % repr(self.sessions.name))
    w("  ttl:                 %d\n" % self.sessions.ttl)
    w("\n")
    w("self.request.\n")
    w(" env         %s\n" % repr(self.request.env))
    w(" get         %s\n" % repr(self.request.get))
    w(" post        %s\n" % repr(self.request.post))
    w(" files       %s\n" % repr(self.request.files))
    w(" cookies     %s\n" % repr(self.request.cookies))
    w(" input       %s\n" % repr(self.request.input.read()))
    w(" url         %s\n" % self.request.url)
    w(" session_id: %s\n" % repr(self.request.session_id))
    w(" session:    %s\n" % repr(self.request.session))
    w(" reconstructed headers:\n%s\n" % '\n'.join(headers))
    w("\n")
    w("self.response.\n")
    w(" custom headers:\n%s\n" % '\n'.join(self.response.headers))
    w("\n")
    w("Query parameters (GET):\n")
    for k,v in self.request.get.items():
      w(k.encode(self.encoding))
      w(" = ")
      try:
        w(v.encode(self.encoding))
      except:
        w(repr(v))
      w("\n")
    w("\n")
    w("Form data (POST):\n")
    for k,v in self.request.post.items():
      w(k.encode(self.encoding))
      w(" = ")
      try:
        w(v.encode(self.encoding))
      except:
        w(repr(v))
      w("\n")
    w("\n")
    w("Cookies:\n")
    try:
      for k,v in self.request.cookies.items():
        w(k.encode(self.encoding))
        w(" = ")
        try:
          w(v.encode(self.encoding))
        except:
          w(repr(v))
        w("\n")
    except:
      w(repr(self.request.cookies))
    w("\n")
  

if __name__ == '__main__':
  from smisk.util.main import main
  main(MyApp)
