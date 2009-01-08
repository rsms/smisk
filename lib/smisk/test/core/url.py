#!/usr/bin/env python
# encoding: utf-8
from smisk.test import *
from smisk.core import URL

class URLTests(TestCase):
  def test_encode_decode(self):
    raw = "http://abc.se:12/mos/jäger/grek land/hej.html?mos=japp&öland=nej#ge-mig/då";
    escaped = URL.escape(raw)
    assert escaped == 'http%3A//abc.se%3A12/mos/j%C3%A4ger/grek%20land/hej.html'\
      '?mos=japp&%C3%B6land=nej%23ge-mig/d%C3%A5'
    encoded = URL.encode(raw)
    assert encoded == 'http%3A%2F%2Fabc.se%3A12%2Fmos%2Fj%C3%A4ger%2Fgrek%20land%2Fhej.html%3Fmos%3Djapp'\
      '%26%C3%B6land%3Dnej%23ge-mig%2Fd%C3%A5'
    assert URL.decode(escaped) == raw
    assert URL.decode(encoded) == raw
    assert URL.unescape(escaped) == URL.decode(escaped)
    self.assertEquals(URL.decode("foo%2Bbar@internets.com"), "foo+bar@internets.com")
  
  def test_encode_decode_string_type(self):
    self.assertEquals(type(URL.encode(u"foo+bar@internets.com")), type(u"foo%2Bbar@internets.com"))
    self.assertEquals(type(URL.encode("foo+bar@internets.com")), type("foo%2Bbar@internets.com"))
    self.assertEquals(type(URL.escape(u"foo+bar@internets.com")), type(u"foo%2Bbar@internets.com"))
    self.assertEquals(type(URL.escape("foo+bar@internets.com")), type("foo%2Bbar@internets.com"))
    self.assertEquals(type(URL.decode(u"foo%2Bbar@internets.com")), type(u"foo+bar@internets.com"))
    self.assertEquals(type(URL.decode("foo%2Bbar@internets.com")), type("foo+bar@internets.com"))
  
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
    
    u = URL('https://john@www.mos.tld/some/path.ext?arg1=245&arg2=hej%20du#chapter5')
    assert u.scheme == 'https'
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
  
  
  def test_decompose_query(self):
    u = URL('http://a/?email=foo%2Bbar@internets.com&&stale_key&&mos=abc&mos=123&&&')
    q = URL.decompose_query(u.query)
    self.assertEquals(q['email'], "foo+bar@internets.com")
    self.assertEquals(q['stale_key'], None)
    self.assertEquals(q['mos'], ['abc', '123'])
    self.assertContains(q.keys(), ['email', 'stale_key', 'mos'])
  
  def test_decompose_query_decode(self):
    u = URL('http://a/?name=%E5%E4%F6')
    q = URL.decompose_query(u.query, encoding='latin-1')
    self.assertTrue(isinstance(q['name'], unicode))
    self.assertEquals(q['name'], u'\xe5\xe4\xf6')
    
    u = URL('http://a/?name=%E5%E4%F6')
    self.assertRaises(UnicodeDecodeError, lambda: URL.decompose_query(u.query, encoding='utf-8'))
    
    u = URL('http://a/?name=%C3%A5%C3%A4%C3%B6%EF%A3%BF')
    q = URL.decompose_query(u.query, encoding='utf-8')
    self.assertTrue(isinstance(q['name'], unicode))
    self.assertEquals(q['name'], u'\xe5\xe4\xf6\uf8ff')
  
  def test_decompose_query_embedded_unicode_for_non_unicode_charsets(self):
    '''Clients acting within a non-unicode compliant charset, like Latin-1, sends
    out-of-charset characters entity-encoded in unicode-order.
    
    i.e. the Apple becomes '%26%2363743%3B' -> '&#63743;'.
    
    Because Smisk is purely unicode on the inside, we care for decoding this data.
    '''
    u = URL('http://a/?symbol=%26%2363743%3B')
    q = URL.decompose_query(u.query, encoding='latin-1') # encoding shouldnt matter in this case
    self.assertEquals(q['symbol'], u'\uf8ff') # xxx currently this test fail because we have not implemented decoding of these kind of entities (yet).
    
  
  def test_to_s_1(self):
    raw = 'http://john:secret@fisk.tld:1983/some/path.ext?arg1=245&arg2=hej%20du#chapter5'
    u = URL(raw)
    self.assertEquals(u.to_s(), raw)
    self.assertEquals(str(u), raw)
    self.assertEquals(unicode(u), unicode(raw))
  
  def test_to_s_2_port(self):
    u = URL('http://fisk.tld:1983/some/path')
    self.assertEquals(u.to_s(port=0), 'http://fisk.tld/some/path')
    self.assertEquals(u.to_s(port80=0), 'http://fisk.tld:1983/some/path')
    self.assertEquals(u.to_s(port=0, port80=1), 'http://fisk.tld/some/path')
    u = URL('http://fisk.tld:80/some/path')
    self.assertEquals(u.to_s(port=0), 'http://fisk.tld/some/path')
    self.assertEquals(u.to_s(port80=0), 'http://fisk.tld/some/path')
    self.assertEquals(u.to_s(port=0, port80=1), 'http://fisk.tld/some/path')
  
  def test_to_s_3(self):
    u = URL('http://john:secret@fisk.tld:1983/some/path.ext?arg1=245&arg2=hej%20du#chapter5')
    
    # meet and greet
    self.assertEquals(u.to_s(scheme=0, user=1, password=1, host=1, port=1, path=1, query=1, fragment=1), 'john:secret@fisk.tld:1983/some/path.ext?arg1=245&arg2=hej%20du#chapter5')
    self.assertEquals(u.to_s(scheme=1, user=0, password=1, host=1, port=1, path=1, query=1, fragment=1), 'http://fisk.tld:1983/some/path.ext?arg1=245&arg2=hej%20du#chapter5')
    self.assertEquals(u.to_s(scheme=1, user=1, password=0, host=1, port=1, path=1, query=1, fragment=1), 'http://john@fisk.tld:1983/some/path.ext?arg1=245&arg2=hej%20du#chapter5')
    self.assertEquals(u.to_s(scheme=1, user=1, password=1, host=0, port=1, path=1, query=1, fragment=1), 'http://john:secret@:1983/some/path.ext?arg1=245&arg2=hej%20du#chapter5')
    self.assertEquals(u.to_s(scheme=1, user=1, password=1, host=1, port=0, path=1, query=1, fragment=1), 'http://john:secret@fisk.tld/some/path.ext?arg1=245&arg2=hej%20du#chapter5')
    self.assertEquals(u.to_s(scheme=1, user=1, password=1, host=1, port=1, path=0, query=1, fragment=1), 'http://john:secret@fisk.tld:1983?arg1=245&arg2=hej%20du#chapter5')
    self.assertEquals(u.to_s(scheme=1, user=1, password=1, host=1, port=1, path=1, query=0, fragment=1), 'http://john:secret@fisk.tld:1983/some/path.ext#chapter5')
    self.assertEquals(u.to_s(scheme=1, user=1, password=1, host=1, port=1, path=1, query=1, fragment=0), 'http://john:secret@fisk.tld:1983/some/path.ext?arg1=245&arg2=hej%20du')
    
    # no scheme
    self.assertEquals(u.to_s(scheme=0, user=0, password=1, host=1, port=1, path=1, query=1, fragment=1), 'fisk.tld:1983/some/path.ext?arg1=245&arg2=hej%20du#chapter5')
    self.assertEquals(u.to_s(scheme=0, user=1, password=0, host=1, port=1, path=1, query=1, fragment=1), 'john@fisk.tld:1983/some/path.ext?arg1=245&arg2=hej%20du#chapter5')
    self.assertEquals(u.to_s(scheme=0, user=1, password=1, host=0, port=1, path=1, query=1, fragment=1), 'john:secret@:1983/some/path.ext?arg1=245&arg2=hej%20du#chapter5')
    self.assertEquals(u.to_s(scheme=0, user=1, password=1, host=1, port=0, path=1, query=1, fragment=1), 'john:secret@fisk.tld/some/path.ext?arg1=245&arg2=hej%20du#chapter5')
    self.assertEquals(u.to_s(scheme=0, user=1, password=1, host=1, port=1, path=0, query=1, fragment=1), 'john:secret@fisk.tld:1983?arg1=245&arg2=hej%20du#chapter5')
    self.assertEquals(u.to_s(scheme=0, user=1, password=1, host=1, port=1, path=1, query=0, fragment=1), 'john:secret@fisk.tld:1983/some/path.ext#chapter5')
    self.assertEquals(u.to_s(scheme=0, user=1, password=1, host=1, port=1, path=1, query=1, fragment=0), 'john:secret@fisk.tld:1983/some/path.ext?arg1=245&arg2=hej%20du')
    
    # no user
    self.assertEquals(u.to_s(scheme=1, user=0, password=0, host=1, port=1, path=1, query=1, fragment=1), 'http://fisk.tld:1983/some/path.ext?arg1=245&arg2=hej%20du#chapter5')
    self.assertEquals(u.to_s(scheme=1, user=0, password=1, host=0, port=1, path=1, query=1, fragment=1), 'http://:1983/some/path.ext?arg1=245&arg2=hej%20du#chapter5')
    self.assertEquals(u.to_s(scheme=1, user=0, password=1, host=1, port=0, path=1, query=1, fragment=1), 'http://fisk.tld/some/path.ext?arg1=245&arg2=hej%20du#chapter5')
    self.assertEquals(u.to_s(scheme=1, user=0, password=1, host=1, port=1, path=0, query=1, fragment=1), 'http://fisk.tld:1983?arg1=245&arg2=hej%20du#chapter5')
    self.assertEquals(u.to_s(scheme=1, user=0, password=1, host=1, port=1, path=1, query=0, fragment=1), 'http://fisk.tld:1983/some/path.ext#chapter5')
    self.assertEquals(u.to_s(scheme=1, user=0, password=1, host=1, port=1, path=1, query=1, fragment=0), 'http://fisk.tld:1983/some/path.ext?arg1=245&arg2=hej%20du')
    
    # no password
    self.assertEquals(u.to_s(scheme=1, user=1, password=0, host=0, port=1, path=1, query=1, fragment=1), 'http://john@:1983/some/path.ext?arg1=245&arg2=hej%20du#chapter5')
    self.assertEquals(u.to_s(scheme=1, user=1, password=0, host=1, port=0, path=1, query=1, fragment=1), 'http://john@fisk.tld/some/path.ext?arg1=245&arg2=hej%20du#chapter5')
    self.assertEquals(u.to_s(scheme=1, user=1, password=0, host=1, port=1, path=0, query=1, fragment=1), 'http://john@fisk.tld:1983?arg1=245&arg2=hej%20du#chapter5')
    self.assertEquals(u.to_s(scheme=1, user=1, password=0, host=1, port=1, path=1, query=0, fragment=1), 'http://john@fisk.tld:1983/some/path.ext#chapter5')
    self.assertEquals(u.to_s(scheme=1, user=1, password=0, host=1, port=1, path=1, query=1, fragment=0), 'http://john@fisk.tld:1983/some/path.ext?arg1=245&arg2=hej%20du')
    
    # no host
    self.assertEquals(u.to_s(scheme=1, user=1, password=1, host=0, port=0, path=1, query=1, fragment=1), 'http://john:secret@/some/path.ext?arg1=245&arg2=hej%20du#chapter5')
    self.assertEquals(u.to_s(scheme=1, user=1, password=1, host=0, port=1, path=0, query=1, fragment=1), 'http://john:secret@:1983?arg1=245&arg2=hej%20du#chapter5')
    self.assertEquals(u.to_s(scheme=1, user=1, password=1, host=0, port=1, path=1, query=0, fragment=1), 'http://john:secret@:1983/some/path.ext#chapter5')
    self.assertEquals(u.to_s(scheme=1, user=1, password=1, host=0, port=1, path=1, query=1, fragment=0), 'http://john:secret@:1983/some/path.ext?arg1=245&arg2=hej%20du')
    
    # no port
    self.assertEquals(u.to_s(scheme=1, user=1, password=1, host=1, port=0, path=0, query=1, fragment=1), 'http://john:secret@fisk.tld?arg1=245&arg2=hej%20du#chapter5')
    self.assertEquals(u.to_s(scheme=1, user=1, password=1, host=1, port=0, path=1, query=0, fragment=1), 'http://john:secret@fisk.tld/some/path.ext#chapter5')
    self.assertEquals(u.to_s(scheme=1, user=1, password=1, host=1, port=0, path=1, query=1, fragment=0), 'http://john:secret@fisk.tld/some/path.ext?arg1=245&arg2=hej%20du')
    
    # no path
    self.assertEquals(u.to_s(scheme=1, user=1, password=1, host=1, port=1, path=0, query=0, fragment=1), 'http://john:secret@fisk.tld:1983#chapter5')
    self.assertEquals(u.to_s(scheme=1, user=1, password=1, host=1, port=1, path=0, query=1, fragment=0), 'http://john:secret@fisk.tld:1983?arg1=245&arg2=hej%20du')
    
    # no query
    self.assertEquals(u.to_s(scheme=1, user=1, password=1, host=1, port=1, path=1, query=0, fragment=0), 'http://john:secret@fisk.tld:1983/some/path.ext')
  

def suite():
  return unittest.TestSuite([
    unittest.makeSuite(URLTests),
  ])

def test():
  runner = unittest.TextTestRunner()
  return runner.run(suite())

if __name__ == "__main__":
  test()
