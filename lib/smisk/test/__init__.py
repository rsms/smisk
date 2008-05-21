#!/usr/bin/env python
# encoding: utf-8
import unittest
from smisk.test import regression, inflection, routing

def suite():
  return unittest.TestSuite(
    (regression.suite(), inflection.suite(), routing.suite())
  )

def test():
  runner = unittest.TextTestRunner()
  return runner.run(suite())

if __name__ == "__main__":
  test()
