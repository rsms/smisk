#!/usr/bin/env python
# encoding: utf-8
import sys, os
from smisk import *

class MyApp(Application):
  def service(self):
    self.response.headers = ["Content-Type: text/plain"]
    
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
    w("self: %s\n" % repr(self))
    w("\n")
    w("self.\n")
    w(" request_class:       %s\n" % repr(self.request_class))
    w(" response_class       %s\n" % repr(self.response_class))
    w(" session_store_class: %s\n" % repr(self.session_store_class))
    w(" session_store:       %s\n" % repr(self.session_store))
    w(" session_id_size:     %s\n" % repr(self.session_id_size))
    w(" session_name:        %s\n" % repr(self.session_name))
    w("\n")
    w("self.request.\n")
    w(" env      %s\n" % repr(self.request.env))
    w(" get      %s\n" % repr(self.request.get))
    w(" post     %s\n" % repr(self.request.post))
    w(" files    %s\n" % repr(self.request.files))
    w(" cookies  %s\n" % repr(self.request.cookies))
    w(" input    %s\n" % repr(self.request.input.read()))
    w(" url      %s\n" % self.request.url)
    w(" session: %s\n" % repr(self.request.session))
    w("\n")
    w("self.response.\n")
    w(" headers  %s\n" % repr(self.response.headers))
  

try:
  if len(sys.argv) > 1:
    print 'Binding to %s' % repr(sys.argv[1])
    bind(sys.argv[1])
  MyApp().run()
except KeyboardInterrupt:
  pass
except:
  import traceback
  traceback.print_exc(1000, open(os.path.abspath(os.path.dirname(__file__)) + "/process-error.log", "a"))
