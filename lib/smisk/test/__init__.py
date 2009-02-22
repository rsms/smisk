#!/usr/bin/env python
# encoding: utf-8
'''Unit test suite.
'''
import unittest, sys, os

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
        raise AssertionError(u'%r !contains %r' % (collection1, collection2))
  

def load_suites(module_names):
  suites = []
  if isinstance(module_names, str):
    module_names = module_names.strip().split('\n')
  for modname in module_names:
    modname = modname.strip()
    if modname:
      __import__(modname)
      mod = sys.modules[modname]
      try:
        suites.append(getattr(mod, 'suite')())
      except AttributeError, e:
        if "has no attribute 'suite'" in e.args[0]:
          e.args = ('module %s has no suite' % mod,)
        raise e
  return suites

def suite():
  suites = load_suites('''
    smisk.test.config
    smisk.test.core.url
    smisk.test.core.xml
    smisk.test.inflection
    smisk.test.mvc.control
    smisk.test.mvc.routing
    smisk.test.serialization
    smisk.test.util.introspect
    smisk.test.util.string_
  ''')
  return unittest.TestSuite(suites)

def test():
  runner = unittest.TextTestRunner()
  return runner.run(suite())

if __name__ == "__main__":
  test()
