#!/usr/bin/env python
# encoding: utf-8
import sys, os
from smisk.core import *

class MyApp(Application):
  def __init__(self, *args, **kwargs):
    super(MyApp, self).__init__(*args, **kwargs)
    # Set a very low session TTL for easy demonstration
    self.sessions.ttl = 10
    self.charset = 'iso-8859-1'
  
  def application_will_start(self):
    # Apply request input limits (reaaaally low, for testing purposes)
    self.request.max_multipart_size = 1024*1024 # 1 MB
    self.request.max_formdata_size = 51 # 51 bytes is exactly the amount of the default values in index.html
  
  def service(self):
    self.response.headers = ["Content-Type: text/plain;charset=" + self.charset]
    
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
    self.response(
      "self. %s\n" % repr(self),
      " request_class:       %s\n" % repr(self.request_class),
      " response_class       %s\n" % repr(self.response_class),
      " sessions_class: %s\n" % repr(self.sessions_class),
      " sessions.       %s\n" % repr(self.sessions),
      "  name:                %s\n" % repr(self.sessions.name),
      "  ttl:                 %d\n" % self.sessions.ttl,
      "\n",
      "self.request.\n",
      " env         %s\n" % repr(self.request.env),
      " get         %s\n" % repr(self.request.get),
      " post        %s\n" % repr(self.request.post),
      " files       %s\n" % repr(self.request.files),
      " cookies     %s\n" % repr(self.request.cookies),
      " input       %s\n" % repr(self.request.input.read()),
      " url         %s\n" % self.request.url,
      " session_id: %s\n" % repr(self.request.session_id),
      " session:    %s\n" % repr(self.request.session),
      " reconstructed headers:\n%s\n" % '\n'.join(headers),
      "\n",
      "self.response.\n",
      " custom headers:\n%s\n" % '\n'.join(self.response.headers),
      "\n",
      "Query parameters (GET):\n"
    )
    
    # More info
    w = self.response.write
    for k,v in self.request.get.items():
      w(k)
      w(" = ")
      try:
        w(v)
      except:
        w(repr(v))
      w("\n")
    w("\n")
    w("Form data (POST):\n")
    for k,v in self.request.post.items():
      w(k.encode(self.charset))
      w(" = ")
      try:
        w(v)
      except:
        w(repr(v))
      w("\n")
    w("\n")
    w("Cookies:\n")
    try:
      for k,v in self.request.cookies.items():
        w(k.encode(self.charset))
        w(" = ")
        try:
          w(v)
        except:
          w(repr(v))
        w("\n")
    except:
      w(repr(self.request.cookies))
    w("\n")
  

if __name__ == '__main__':
  from smisk.util.main import main
  main(MyApp)
