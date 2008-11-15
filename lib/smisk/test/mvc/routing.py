#!/usr/bin/env python
# encoding: utf-8
from smisk.test import *
from smisk.mvc import *
from smisk.mvc.routing import *
from smisk.mvc.control import *
import smisk.mvc.http as http

from test_matter import *

echo = False
if __name__ == '__main__':
  echo = True
  print 'Printing out loud because __name__ == __main__ --> self.echo = True'

class RoutingTests(TestCase):
  '''Tests covering the `smisk.mvc.routing` module.
  '''
  def setUp(self):
    self.router = Router()
    self.router.filter(r'^/user/(?P<user>[^/]+)', '/level2/show_user')
    self.router.filter(r'^/archive/(\d{4})/(\d{2})/(\d{2})', '/level2/level3', regexp_flags=0)
  
  def test1_basic(self):
    self.assertRoute('/', '/')
    self.assertRoute('/func_on_root', '/func_on_root')
    self.assertRoute('/level2', '/level2')
    self.assertRoute('/level2/func_on_level2', '/level2/func_on_level2')
    self.assertRoute('/level2/func_on_level2/nothing/here', http.NotFound)
    self.assertRoute('/level2/nothing/here', http.NotFound)
    self.assertRoute('/level2/level3', '/level2/level3')
    self.assertRoute('/level2/LEVEL3', '/level2/level3')
    self.assertRoute('/level2/level3/__call__', http.NotFound)
    self.assertRoute('/level3', http.NotFound)
    self.assertRoute('/level2/level3/func_on_level3', '/level2/level3/func_on_level3')
  
  def test2_filtered(self):
    self.assertRoute('/user/rasmus/photos', '/level2/show_user')
    self.assertRoute('/user/rasmus', '/level2/show_user')
    self.assertRoute('/USER/rasmus', '/level2/show_user')
    self.assertRoute('/user', http.NotFound)
    self.assertRoute('/archive/2008/01/15', '/level2/level3')
    self.assertRoute('/ARCHIVE/2009/10/21/foo', http.NotFound)
    self.assertRoute('/level2/level3/posts/list', '/level2/level3/posts/list')
  
  def test3_non_delegating(self):
    """Trying to access inherited leafs which does not delegate calls"""
    self.assertRoute('/level2/level3/func_on_level2', http.NotFound)
    self.assertRoute('/level2/level3/posts/func_on_level2', http.NotFound)
    self.assertRoute('/level2/level3/posts/', http.NotFound)
  
  def test4_delegating(self):
    """Access inherited leafs which do delegate calls"""
    self.assertRoute('/level2/delegating_func_on_root', '/delegating_func_on_root')
    self.assertRoute('/level2/level3/delegating_func_on_root', '/delegating_func_on_root')
    self.assertRoute('/level2/level3/posts/delegating_func_on_root', '/delegating_func_on_root')
  
  def test5_renamed(self):
    """Access renamed nodes, for example by @expose(name=)"""
    self.assertRoute('/level2/foo-bar', '/level2/foo-bar')
    self.assertRoute('/level2/foo_bar', http.NotFound)
    self.assertRoute('/level2/level-3-b/func_on_level3B', '/level2/level-3-b/func_on_level3B')
    self.assertRoute('/level2/level3B/func_on_level3B', http.NotFound)
  
  def test6_hidden(self):
    self.assertRoute('/level2/level3/hidden_method_on_level3', http.NotFound)
  
  def test7_protected_on_Controller(self):
    self.assertRoute('/controller_name', http.NotFound)
    self.assertRoute('/controller_path', http.NotFound)
    self.assertRoute('/controller_uri', http.NotFound)
    self.assertRoute('/special_methods', http.NotFound)
    self.assertRoute('/__new__', http.NotFound)
  
  def test8_explicitly_named_args(self):
    self.assertRoute('/one_named_arg1', '/one_named_arg1?foo=bar', {'foo':'bar'})
    self.assertRoute('/one_named_arg2', '/one_named_arg2?foo=bar', {'foo':'bar'})
    self.assertRoute('/one_named_arg3', '/one_named_arg3?foo=bar', {'foo':'bar'})
    self.assertRoute('/one_named_arg4', '/one_named_arg4?foo=bar', {'foo':'bar'})
  
  def test9_special_builtins(self):
    # These should succeed
    special_names = Controller.special_methods().keys()
    not_found_tests = []
    for name in special_names:
      not_found_tests.append(('/level2/%s' % name, http.NotFound))
      dest, args, params = self.router(URL('/%s' % name), [], {})
      self.assertTrue(dest())
    # These should fail
    self.assertRoutes(*not_found_tests)
  
  def test10_params(self):
    self.assertRoute('/level2/show_user', http.BadRequest)
    self.assertRoute('/level2/show_user', '/level2/show_user', {'user':'john'})
  
  def assertRoutes(self, router=None, *urls):
    for t in urls:
      self.assertRoute(*t)
  
  def assertRoute(self, url, expected_return, params={}, router=None):
    if router is None:
      r = self.router
    else:
      r = router
    url = URL(url)
    if echo:
      print '\nRouting \'%s\' expected to return %r (params=%s)' % (url, expected_return, params)
    dest, args, params = r(url, [], params)
    if isinstance(expected_return, http.Status):
      try:
        dest_returned = dest()
        assert r == 0, 'should raise %r but did not raise any exception '\
          'at all. dest() returned %r' % (expected_return, dest_returned)
      except http.HTTPExc, e:
        assert isinstance(e.status, expected_return.__class__), '%r (%x) != %r (%x)' %\
          (expected_return, id(expected_return), e.status, id(e.status))
      except AssertionError:
        raise
      except Exception, e:
        assert 0, 'should have raised %r, but instead %r was raised' %\
          (expected_return, e)
    else:
      if dest is not None:
        if echo:
          print 'Calling %r(*%s, **%s)' % (dest, args, params)
        returned = dest(*args, **params)
      else:
        returned = Nothing
      assert returned == expected_return, '%s != %s' % (returned, expected_return)
  

def suite():
  return unittest.TestSuite([
    unittest.makeSuite(RoutingTests),
  ])

def test():
  runner = unittest.TextTestRunner()
  return runner.run(suite())

if __name__ == "__main__":
  test()
