#!/usr/bin/env python
# encoding: utf-8
import unittest
from serialization import HTTPConduit

class SerializationTest(unittest.TestCase):
  def test_plural(self):
		h = HTTPConduit()
		h.read()
	

def suite():
  return unittest.TestSuite([ unittest.makeSuite(SerializationTest) ])

def test():
  runner = unittest.TextTestRunner()
  return runner.run(suite())

if __name__ == "__main__":
  test()
