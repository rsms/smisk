#!/usr/bin/env python
# encoding: utf-8
import os, logging
from smisk.mvc import main
import controllers

if __name__ == '__main__':
  models.setup_all()
  models.create_all()
  main(
    appdir=os.path.dirname(os.path.dirname(__file__)),
    log_level=logging.DEBUG,
    autoreload=True
  )
