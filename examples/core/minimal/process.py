#!/usr/bin/env python
# encoding: utf-8
from smisk.core import Application

class MyApp(Application):
  def service(self):
    self.response("Hello World!")

MyApp().run()
