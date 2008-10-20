#!/usr/bin/env python
# encoding: utf-8
from smisk.test import *

class SerializationTest(TestCase):
  pass

def suite():
  return unittest.TestSuite([ unittest.makeSuite(SerializationTest) ])

def test():
  runner = unittest.TextTestRunner()
  return runner.run(suite())

if __name__ == "__main__":
  test()
