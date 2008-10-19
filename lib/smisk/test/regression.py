#!/usr/bin/env python
# encoding: utf-8
import unittest

import smisk.core.xml as xml

class XMLTests(unittest.TestCase):
  def setUp(self):
    pass
  
  def test_encode(self):
    encoded = xml.escape('Some <document> with strings & characters with should be "escaped"')
    expected = 'Some &#x3C;document&#x3E; with strings &#x26; characters with should be &#x22;escaped&#x22;'
    assert encoded == expected
  

from smisk import URL

class URLTests(unittest.TestCase):
  def test_codec(self):
    raw = "http://abc.se:12/mos/jäger/grek land/hej.html?mos=japp&öland=nej#ge-mig/då";
    escaped = URL.escape(raw)
    assert escaped == 'http%3A//abc.se%3A12/mos/j%C3%A4ger/grek%20land/hej.html?mos=japp&%C3%B6land=nej%23ge-mig/d%C3%A5'
    encoded = URL.encode(raw)
    assert encoded == 'http%3A%2F%2Fabc.se%3A12%2Fmos%2Fj%C3%A4ger%2Fgrek%20land%2Fhej.html%3Fmos%3Djapp%26%C3%B6land%3Dnej%23ge-mig%2Fd%C3%A5'
    assert URL.decode(escaped) == raw
    assert URL.decode(encoded) == raw
    assert URL.unescape(escaped) == URL.decode(escaped)
  
  def test_clean_strings(self):
    # Should be unmodified and retain pointers
    raw = 'hello/john'
    escaped = URL.escape(raw)
    assert escaped == raw
    assert id(escaped) == id(raw)
    
    raw = 'hello_john'
    encoded = URL.encode(raw)
    assert encoded == raw
    assert id(encoded) == id(raw)
  
  def test_parse(self):
    u = URL('http://john:secret@www.mos.tld/some/path.ext?arg1=245&arg2=hej%20du#chapter5')
    assert u.scheme == 'http'
    assert u.user == 'john'
    assert u.password == 'secret'
    assert u.host == 'www.mos.tld'
    assert u.path == '/some/path.ext'
    assert u.query == 'arg1=245&arg2=hej%20du'
    assert u.fragment == 'chapter5'
    
    u = URL('http://john@www.mos.tld/some/path.ext?arg1=245&arg2=hej%20du#chapter5')
    assert u.scheme == 'http'
    assert u.user == 'john'
    assert u.password == None
    assert u.host == 'www.mos.tld'
    assert u.path == '/some/path.ext'
    assert u.query == 'arg1=245&arg2=hej%20du'
    assert u.fragment == 'chapter5'
    
    u = URL('http://www.mos.tld/some/path.ext?arg1=245&arg2=hej%20du-chapter5')
    assert u.query == 'arg1=245&arg2=hej%20du-chapter5'
    assert u.fragment == None
    
    u = URL('http://www.mos.tld/some/path.ext?arg1=245&arg2=hej%20du?chapter5')
    assert u.query == 'arg1=245&arg2=hej%20du?chapter5'
    assert u.fragment == None
    
    u = URL('http://www.mos.tld/some/path.ext?')
    assert u.query == ''
    assert u.fragment == None
    
    u = URL('http://www.mos.tld/some/path.ext#arg1=245&arg2=hej%20du-chapter5')
    assert u.query == None
    assert u.fragment == 'arg1=245&arg2=hej%20du-chapter5'
    
    u = URL('http://www.mos.tld/some/path.ext#arg1=245&arg2=hej%20du?chapter5')
    assert u.query == None
    assert u.fragment == 'arg1=245&arg2=hej%20du?chapter5'
    
    u = URL('http://www.mos.tld/some/path.ext#')
    assert u.query == None
    assert u.fragment == ''
  

from smisk.util import introspect, Undefined

class IntrospectTests(unittest.TestCase):
  def setUp(self):
    class A(object):
      def hello(self, one, two, three=None, four=123, five='internets'):
        foo = 'oof'
        bar = 'rab'
        two = 14
        for baz in foo:
          pass
        return locals()
      def ping(self, filter=None, *argz, **kwargz):
        pass
    
    self.A = A
    self.expect_hello_info = {
      'name': 'hello', 
      'args': [
        ('one', Undefined),
        ('two', Undefined),
        ('three', None),
        ('four', 123),
        ('five', 'internets')
      ], 
      'varargs': False,
      'kwargs': False,
      'locals': ('foo', 'bar', 'baz')
    }
  
  def test_1_info(self):
    a = self.A()
    assert introspect.callable_info(a.hello) == self.expect_hello_info
  
  def test_2_ensure_va_kwa(self):
    a = self.A()
    try:
      assert a.hello(1,2,3,4,5,*('extra va1','extra va2')) == 0,\
        'should throw TypeError'
    except TypeError:
      pass
    
    a.hello = introspect.ensure_va_kwa(a.hello)
    
    expect_hello_info = self.expect_hello_info.copy()
    expect_hello_info['varargs'] = True
    expect_hello_info['kwargs'] = True
    assert introspect.callable_info(a.hello) == expect_hello_info
    
    assert a.hello(1,2,3,4,5, *('va1','va2'), **{'kw1':1, 'kw2':2}) == {
      'self': a,
      'one': 1,
      'two': 14,
      'three': 3,
      'four': 4,
      'five': 5,
      'foo':'oof',
      'bar':'rab',
      'baz':'f'
    }
    assert a.hello('ett', 'tva') == {
      'self': a,
      'one': 'ett',
      'two': 14,
      'three': None,
      'four': 123,
      'five': 'internets',
      'foo':'oof',
      'bar':'rab',
      'baz':'f'
    }
  

def suite():
  return unittest.TestSuite([
    unittest.makeSuite(URLTests),
    unittest.makeSuite(XMLTests),
    unittest.makeSuite(IntrospectTests),
  ])

def test():
  runner = unittest.TextTestRunner()
  return runner.run(suite())

if __name__ == "__main__":
  test()
