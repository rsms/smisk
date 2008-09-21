#!/usr/bin/env python
# encoding: utf-8
from smisk.mvc import Controller, main

class Root(Controller):
  def __call__(self, *args, **params):
    return {'message': 'Hello World!'}

if __name__ == '__main__':
  main()
