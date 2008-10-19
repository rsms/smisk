#!/usr/bin/env python
# encoding: utf-8
from smisk.mvc import *

class root(Controller):
  # This is an alias "/" --> "/smisk:methods"
  __call__ = Controller._methods
  
  def echo(self, *args, **params):
    '''Echoes input arguments and parameters back.'''
    return dict(args=args, params=params)
  
  @expose('grodan', formats=['xml', 'html'])
  def moset(self):
    return {'moset': ['bakat', 'gott']}

main(autoreload=True)
