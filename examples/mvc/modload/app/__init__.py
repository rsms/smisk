#!/usr/bin/env python
# encoding: utf-8
import os
from smisk.mvc import Application as App
from smisk.mvc.control import Controller

class ApplicationController(Controller):
  def index(self, **params):
    return 'Hello world'
  

if __name__ == '__main__':
  App.main(os.path.dirname(__file__))
