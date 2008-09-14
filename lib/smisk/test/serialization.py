#!/usr/bin/env python
# encoding: utf-8
import unittest

class SerializationTest(unittest.TestCase):
  def test_plural(self):
		pass
	

def suite():
  return unittest.TestSuite([ unittest.makeSuite(SerializationTest) ])

def test():
  runner = unittest.TextTestRunner()
  return runner.run(suite())

if __name__ == "__main__":
  test()
