#!/usr/bin/env python
# encoding: utf-8
import sys, os, unittest
from smisk.test.live import LiveTestCase, suite_if_possible

class NegotiateCharset(LiveTestCase):
  def runTest(self):
    client = self.connection()
    
    rsp = client.request('GET', '/', headers=[
      ('Accept','text/html,application/xml;q=0.9,*/*;q=0.8'),
      ('Accept-Charset','ISO-8859-1,utf-8;q=0.7,*;q=0.7'),
    ])
    
    self.assertTrue(rsp.is_ok)
    
    self.assertResponseHeaderIsSet(rsp, 'content-length')
    self.assertResponseHeaderEquals(rsp, 'content-type', 'text/html; charset=utf-8')
    self.assertResponseHeaderEquals(rsp, 'content-location', '/.html')
    
    self.assertResponseHeaderIsSet(rsp, 'vary')
    for v in rsp.header('vary'):
      self.assertTrue('Accept-Charset' in v)
      self.assertTrue('Accept' in v)
    
    self.assertNotEquals(rsp.body, '')
  

def suite():
  return suite_if_possible(NegotiateCharset)

def test():
  return unittest.TextTestRunner().run(suite())

if __name__ == "__main__":
  import logging
  logging.basicConfig(level=logging.INFO, format="%(name)-40s %(message)s")
  test()
