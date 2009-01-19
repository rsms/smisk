#!/usr/bin/env python
# encoding: utf-8
import sys, os, unittest
from smisk.test.live import LiveTestCase, suite_if_possible

class KVSExample(LiveTestCase):
  def test_0_simple_response(self):
    client = self.connection()
    rsp = client.request('GET', '/', headers=[
      ('Accept','*/*'),
      ('Accept-Charset','utf-8'),
    ])
    payload = eval(rsp.body)
    #print payload
    self.assertTrue('entries' in payload)
    self.assertEquals(len(payload['entries']), 0)
    client.disconnect()
  
  def test_1_put_get_delete_single_connn(self):
    def reconnect(client):
      return client
    self._test_put_get_delete(reconnect)
  
  def test_2_put_get_delete_serial_conns(self):
    def reconnect(client):
      client.disconnect()
      return self.connection()
    #self._test_put_get_delete(reconnect)
  
  def test_3_put_get_delete_parallel_conns(self):
    def reconnect(client):
      return self.connection()
    #self._test_put_get_delete(reconnect)
  
  def _test_put_get_delete(self, reconnect):
    orig_payload = {'value': {'a': u'Aaa', 'b': u'Bee', 'j': u'Jey'}}
    orig_payload_s = repr(orig_payload)
    send_payload_headers = [
      ('Content-type', 'text/x-python'),
      ('Content-length', str(len(orig_payload_s)))
    ]
    
    client = self.connection()
    
    rsp = client.request('PUT', '/entry/a', body=orig_payload_s, headers=send_payload_headers)
    rsp.read() # finish response
    try:
      self.assertTrue(rsp.is_ok, rsp.status)
    except:
      print >> sys.stderr, rsp.body
      raise
    
    client = reconnect(client)
    rsp = client.request('GET', '/entry/a')
    self.assertTrue(rsp.is_ok)
    rsp_payload = eval(rsp.body)
    print rsp_payload
    self.assertTrue('value' in rsp_payload)
    value = rsp_payload['value']
    self.assertEquals(rsp_payload['value']['a'], orig_payload['value']['a'])
    self.assertEquals(rsp_payload['value']['b'], orig_payload['value']['b'])
    self.assertEquals(rsp_payload['value']['j'], orig_payload['value']['j'])
    
    client.disconnect()
  

def unused():
  rsp = self.client.request('GET', '/', headers=[
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

def suite(enable_experimental=False):
  # Currently disabled since we have not managed to properly kill the 
  # various processes that's started during the test.
  if enable_experimental:
    return suite_if_possible(KVSExample)
  else:
    return unittest.TestSuite([])

def test(enable_experimental=False):
  return unittest.TextTestRunner().run(suite(enable_experimental))

if __name__ == "__main__":
  import logging
  logging.basicConfig(level=logging.INFO, format="%(name)-40s %(message)s")
  test(True)
