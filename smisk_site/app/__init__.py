#!/usr/bin/env python
# encoding: utf-8
import os, logging
from smisk.mvc import main
import controllers

if __name__ == '__main__':
  main(
    appdir=os.path.dirname(os.path.dirname(__file__)),
    log_level=logging.DEBUG,
    autoreload=True
  )
