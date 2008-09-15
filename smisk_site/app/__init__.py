#!/usr/bin/env python
# encoding: utf-8
import os, logging
from smisk.mvc import main
from smisk.mvc.template import Templates
import controllers

Templates.errors = {404: 'errors/404'}

if __name__ == '__main__':
  main(
    appdir=os.path.dirname(os.path.dirname(__file__)),
    log_level=logging.DEBUG,
    autoreload=True
  )
