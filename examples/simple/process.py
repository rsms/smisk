#!/usr/bin/env python
# encoding: utf-8
import sys, os
from smisk import *

class MyRequest(Request):
  def acceptsCharsets(self):
    '''Return a list of charsets which the client can handle, ordered by priority and appearing order.'''
    vv = []
    for cs in self.env['HTTP_ACCEPT_CHARSET'].split(','):
      p = cs.find(';')
      if p != -1:
        pp = cs.find('q=', p)
        if pp != -1:
          vv.append([cs[:p], int(float(cs[pp+2:])*100)])
          continue
      vv.append([cs, 100])
    vv.sort(lambda a,b: b[1] - a[1])
    return [v[0] for v in vv]
  

class MyResponse(Response):
  def redirect(self, destination):
    self.headers += ['Location: %s' % destination, 'Status: 302 Found']
  

class MyApp(Application):
  
  chunk = '.'*8000
  
  def __init__(self):
    self.requestClass = MyRequest
    self.responseClass = MyResponse
    Application.__init__(self)
  
  def service(self):
    #self.response.out.write("Content-Length: 8000\r\n\r\n")
    #self.response.out.write(self.chunk)
    
    self.response.headers = ["Content-Type: text/plain"]
    self.response.write("self.request.url = %s\n" % self.request.url)
    self.response.write("HTTP_ACCEPT_CHARSET = %s\n" % self.request.env['HTTP_ACCEPT_CHARSET'])
    self.response.write("self.request.acceptsCharsets() = %s\n" % self.request.acceptsCharsets())
    
    #self.response.write(self.chunk)
    
    #self.response.write("<h1>Hello World!</h1>"
    #  "request.env = <tt>%s</tt>\n" % self.request.env)
    #self.response.headers = ["Content-Type: text/html"]
    #err1()
  

# test exception response
def err1(): err2()
def err2(): err3()
def err3(): err4()
def err4(): err5()
def err5(): raise IOError("Kabooom!")

# test notifications
def notification_handler(notification, *args):
  sys.stderr.write("NOTIFICATION: %s %s\n" % (notification, repr(args)))

nc = NotificationCenter.default()
nc.subscribe(notification_handler, ApplicationWillStartNotification)
nc.subscribe(notification_handler, ApplicationDidStopNotification)
nc.subscribe(notification_handler, ApplicationWillExitNotification)

try:
  MyApp().run()
except KeyboardInterrupt:
  pass
