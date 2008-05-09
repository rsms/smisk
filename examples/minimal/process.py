#!/usr/bin/env python
# encoding: utf-8
from smisk import Application

class MyApp(Application):
  def service(self):
    self.response.write("Hello World!")

MyApp().run()
