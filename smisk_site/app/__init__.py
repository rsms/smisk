#!/usr/bin/env python
# encoding: utf-8
import os, logging
from smisk.mvc import main, Application
from smisk.mvc.template import Templates
import controllers

Templates.errors = {404: 'errors/404'}

if __name__ == '__main__':
  app = Application(
    log_level=logging.DEBUG,
    autoreload=True
  )
  app.routes.map(r'^/docs/(?P<article>.+)', controllers.root().docs)
  main(os.path.dirname(os.path.dirname(__file__)))
