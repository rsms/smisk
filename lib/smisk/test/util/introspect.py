#!/usr/bin/env python
# encoding: utf-8
from smisk.test import *
from smisk.util.introspect import *
from smisk.util.type import Undefined

class A(object):
  def __call__(self):
    pass
  def hello(self, one, two, three=None, four=123, five='internets'):
    foo = 'oof'
    bar = 'rab'
    two = 14
    for baz in foo:
      pass
    return locals()
  def ping(self, filter=None, *argz, **kwargz):
    pass

class B(object):
  def foo(self):
    pass

class IntrospectTests(TestCase):
  def setUp(self):
    self.expect_hello_info = {
      'name': 'hello', 
      'args': (
        ('one', Undefined),
        ('two', Undefined),
        ('three', None),
        ('four', 123),
        ('five', 'internets')
      ),
      'varargs': False,
      'varkw': False,
      'method': True
    }
    
  def test_2_info_methods(self):
    a = A()
    expected = self.expect_hello_info
    returned = introspect.callable_info(a.hello)
    assert returned == expected, '%s\n!=\n%s' % (returned, expected)
    returned = introspect.callable_info(A.hello)
    assert returned == expected, '%s\n!=\n%s' % (returned, expected)
    
    b = B()
    expected = {
      'name':'foo',
      'args': (),
      'method':True,
      'varargs': False,
      'varkw': False
    }
    returned = introspect.callable_info(b.foo)
    assert returned == expected, '%s\n!=\n%s' % (returned, expected)
    returned = introspect.callable_info(B.foo)
    assert returned == expected, '%s\n!=\n%s' % (returned, expected)
  
  def test_2_info_function(self):
    def plain():
      pass
    expected = {
      'name':'plain',
      'method':False,
      'varargs': False,
      'varkw': False,
      'args': (),
    }
    returned = introspect.callable_info(plain)
    assert returned == expected, '%s\n!=\n%s' % (returned, expected)
  
  def test_2_info_function_varargs(self):
    def varargs(a, b=1, *args):
      pass
    expected = {
      'name':'varargs',
      'method':False,
      'varargs': True,
      'varkw': False,
      'args':(
        ('a',Undefined),
        ('b',1)
      ),
    }
    returned = introspect.callable_info(varargs)
    assert returned == expected, '%s\n!=\n%s' % (returned, expected)
  
  def test_2_info_function_varkw(self):
    def foobar(a=[], b=1, **xyz):
      pass
    expected = {
      'name':'foobar',
      'method':False,
      'varargs': False,
      'varkw': True,
      'args':(
        ('a',[]),
        ('b',1)
      ),
    }
    returned = introspect.callable_info(foobar)
    assert returned == expected, '%s\n!=\n%s' % (returned, expected)
  
  def test_3_ensure_va_kwa(self):
    a = A()
    try:
      assert a.hello(1,2,3,4,5,*('extra va1','extra va2')) == 0, 'should throw TypeError'
    except TypeError:
      pass
    a.hello = introspect.ensure_va_kwa(a.hello)
    expected = self.expect_hello_info.copy()
    expected['varargs'] = True
    expected['varkw'] = True
    returned = introspect.callable_info(a.hello)
    assert returned == expected, '%s\n!=\n%s' % (returned, expected)
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
    unittest.makeSuite(IntrospectTests),
  ])

def test():
  runner = unittest.TextTestRunner()
  return runner.run(suite())

if __name__ == "__main__":
  test()
