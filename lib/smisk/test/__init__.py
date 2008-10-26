#!/usr/bin/env python
# encoding: utf-8
'''Unit test suite.
'''
import unittest, os

class TestCase(unittest.TestCase):
  def assertContains(self, collection1, collection2):
    '''Test that all items in `collection1` is contained within `collection2`.
    
    The order of the contained items does not matter.
    
    :param collection1: Collection 1
    :type  collection1: collection
    :param collection2: Collection 2
    :type  collection2: collection
    :rtype: None
    '''
    for item in collection1:
      if item not in collection2:
        raise unittest.AssertionError(u'%r !contains %r' % (collection1, collection2))
  

def suite():
  from smisk.util.python import load_modules
  suites = []
  for m in load_modules(os.path.dirname(__file__), deep=True).values():
    try:
      suites.append(m.suite())
    except AttributeError:
      pass
  return unittest.TestSuite(suites)

def test():
  runner = unittest.TextTestRunner()
  return runner.run(suite())

if __name__ == "__main__":
  test()
