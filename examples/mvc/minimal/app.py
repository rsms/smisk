#!/usr/bin/env python
# encoding: utf-8
from smisk.mvc import *

class root(Controller):
  def __call__(self, **params):
    return {'request parameters': params}

main(autoreload=True)
