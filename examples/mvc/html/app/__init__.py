#!/usr/bin/env python
# encoding: utf-8
import os
from smisk.mvc import main
import controllers, models

if __name__ == '__main__':
  models.setup_all()
  models.create_all()
  main()
