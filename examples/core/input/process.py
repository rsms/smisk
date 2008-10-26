#!/usr/bin/env python
# encoding: utf-8
import sys, os
from smisk.core import *

class MyApp(Application):
  def __init__(self, *args, **kwargs):
    super(MyApp, self).__init__(*args, **kwargs)
    # Set a very low session TTL for easy demonstration
    self.sessions.ttl = 10
  
  def service(self):
    self.response.headers = ["Content-Type: text/plain"]
    
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
    w("\n")
    w("self.response.\n")
    w(" headers     %s\n" % repr(self.response.headers))
  

try:
  # Any arguments means we run stand.alone and should bind to the first argument:
  if len(sys.argv) > 1:
    print 'Binding to %s' % repr(sys.argv[1])
    bind(sys.argv[1])
  MyApp().run()
except KeyboardInterrupt:
  pass
except:
  import traceback
  traceback.print_exc(1000, open(os.path.abspath(os.path.dirname(__file__)) + "/process-error.log", "a"))
