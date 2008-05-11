#!/usr/bin/env python
# encoding: utf-8
from smisk import Application

class MyApp(Application):
  def service(self):
    self.response("Hello World!")

try:
  MyApp().run()
except KeyboardInterrupt:
  pass
