#!/usr/bin/env python
# encoding: utf-8
from smisk.mvc import *

class root(Controller):
  def __call__(self, **params):
    '''Simply returns the request'''
    return params

main(autoreload=True)
