#!/usr/bin/env python
# encoding: utf-8
from smisk.test import *
from smisk.util.string import *
from smisk.core import URL

class StringUtilTests(TestCase):
  def test1_normalize_url(self):
    abs_url = URL('http://www.foo.tld/bar/?arg=12&baz=abc')
    self.assertEquals(normalize_url('/mos', abs_url).__str__(), 'http://www.foo.tld/mos')
    self.assertEquals(normalize_url('mos.html', abs_url).__str__(), 'http://www.foo.tld/bar/mos.html')
    self.assertEquals(normalize_url('mos.html?xyz=987&abc=123', abs_url).__str__(), 'http://www.foo.tld/bar/mos.html?xyz=987&abc=123')
    self.assertEquals(normalize_url('mos.html').__str__(), '/mos.html')
    self.assertEquals(normalize_url('/mos').__str__(), '/mos')
  

def suite():
  return unittest.TestSuite([
    unittest.makeSuite(StringUtilTests),
  ])

def test():
  runner = unittest.TextTestRunner()
  return runner.run(suite())

if __name__ == "__main__":
  test()
