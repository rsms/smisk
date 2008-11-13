#!/usr/bin/env python
# encoding: utf-8
from smisk.test import *
import smisk.core.xml as xml

class XMLTests(TestCase):
  def setUp(self):
    pass
  
  def test_encode(self):
    encoded = xml.escape('Some <document> with strings & characters with should be "escaped"')
    expected = 'Some &#x3C;document&#x3E; with strings &#x26; characters with should be &#x22;escaped&#x22;'
    assert encoded == expected
  

def suite():
  return unittest.TestSuite([
    unittest.makeSuite(XMLTests),
  ])

def test():
  runner = unittest.TextTestRunner()
  return runner.run(suite())

if __name__ == "__main__":
  test()
