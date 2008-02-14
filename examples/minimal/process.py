#!/usr/bin/env python
# encoding: utf-8
from smisk import Application

class MyApp(Application):
  def service(self):
    self.response.headers = ["Content-Type: text/html"]
    self.response.write("<h1>Hello World!</h1>")

try:
  MyApp().run()
except KeyboardInterrupt:
  pass
