#!/usr/bin/env python
# encoding: utf-8
"""
test_URL.py

Created by Rasmus Andersson on 2007-11-11.
Copyright (c) 2007 Spotify Technology S.A.R.L. All rights reserved.
"""

import unittest
from smisk import URL

class test_URL(unittest.TestCase):
  def setUp(self):
    pass
  
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
  

    
if __name__ == '__main__':
  unittest.main()
