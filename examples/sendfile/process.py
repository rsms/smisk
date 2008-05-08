#!/usr/bin/env python
# encoding: utf-8
import sys, os
from smisk import *

class MyApp(Application):
  def service(self):
    if self.request.url.path[-4:] == '.jpg':
      path = os.path.abspath(self.request.url.path.replace('..', '').lstrip('/'))
      sys.stderr.write("Sending file %s\n" % path)
      self.response.send_file(path)
    else:
      self.response.headers = ["Content-Type: text/html"]
      self.response.write("An image which will be sent using X-Sendfile if supported:<br/>")
      self.response.write('<img src="image.jpg" alt="" />')
  

try:
  MyApp().run()
except KeyboardInterrupt:
  pass