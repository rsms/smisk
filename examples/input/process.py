#!/usr/bin/env python
# encoding: utf-8
import sys, os
from smisk import *

class MyApp(Application):
  def service(self):
    self.response.headers = ["Content-Type: text/plain"]
    
    if self.request.get.has_key('set_cookie'):
      self.response.setCookie('a_cookie', self.request.get['set_cookie'])
    
    w = self.response.write
    w("self.request.\n")
    w(" env     %s\n" % repr(self.request.env))
    w(" get     %s\n" % repr(self.request.get))
    w(" post    %s\n" % repr(self.request.post))
    w(" files   %s\n" % repr(self.request.files))
    w(" cookie  %s\n" % repr(self.request.cookie))
    w(" input   %s\n" % repr(self.request.input.read()))
    w(" url     %s\n" % self.request.url)
    #w("session: %s\n" % repr(self.request.session))
  

try:
  MyApp().run()
except KeyboardInterrupt:
  pass