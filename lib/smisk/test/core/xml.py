#!/usr/bin/env python
# encoding: utf-8
from smisk.test import *
import smisk.core.xml as xml

class XMLTests(TestCase):
  def setUp(self):
    pass
  
  def test_encode(self):
    #Encode/escape unsafe character in XML
    encoded = xml.escape('Some <document> with strings & characters which should be "escaped"')
    expected = 'Some &lt;document&gt; with strings &amp; characters which should be &quot;escaped&quot;'
    self.assertEquals(encoded, expected)
  
  
  def test_decode(self):
    #Decode/unescape entities in XML
    decoded = xml.unescape('Some &lt;document&gt; with strings &amp; characters which should be'\
      ' &quot;escaped&quot;')
    expected = 'Some <document> with strings & characters which should be "escaped"'
    self.assertEquals(decoded, expected)
  
  
  def test_string_type_integrity(self):
    #Assure the same string type (bytes or unicode) is output as was input
    self.assertEquals(type(xml.escape(u'foo<bar>"baz"&')), type(u"foo&lt;bar&gt;&quot;baz&quot;&amp;"))
    self.assertEquals(type(xml.escape('foo<bar>"baz"&')), type("foo&lt;bar&gt;&quot;baz&quot;&amp;"))
    self.assertEquals(type(xml.escape(u"foo&lt;bar&gt;&quot;baz&quot;&amp;")), type(u'foo<bar>"baz"&'))
    self.assertEquals(type(xml.escape("foo&lt;bar&gt;&quot;baz&quot;&amp;")), type('foo<bar>"baz"&'))
  

def suite():
  return unittest.TestSuite([
    unittest.makeSuite(XMLTests),
  ])

def test():
  runner = unittest.TextTestRunner()
  return runner.run(suite())

if __name__ == "__main__":
  test()
