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
    self.router.filter(r'^/user/(?P<user>[^/]+)', '/level2/func_on_level2')
    self.router.filter(r'^/archive/(\d{4})/(\d{2})/(\d{2})', '/level2/level3', regexp_flags=0)
  
  def test1_basic(self):
    self.assertRoutes((
      ('/', '/'),
      ('/func_on_root', '/func_on_root'),
      ('/level2', '/level2'),
      ('/level2/func_on_level2', '/level2/func_on_level2'),
      ('/level2/nothing/here', http.NotFound),
      ('/level2/level3', '/level2/level3'),
      ('/level2/LEVEL3', '/level2/level3'),
      ('/level2/level3/__call__', http.NotFound),
      ('/level3', http.NotFound),
      ('/level2/level3/func_on_level3', '/level2/level3/func_on_level3'),
    ))
  
  def test2_filtered(self):
    self.assertRoutes((
      ('/user/rasmus/photos', '/level2/func_on_level2'),
      ('/user/rasmus', '/level2/func_on_level2'),
      ('/USER/rasmus', '/level2/func_on_level2'),
      ('/user', http.NotFound),
      ('/archive/2008/01/15', '/level2/level3'),
      ('/ARCHIVE/2008/01/15/foo', http.NotFound),
      ('/level2/level3/posts/list', '/level2/level3/posts/list'),
    ))
  
  def test3_non_delegating(self):
    """Trying to access inherited leafs which does not delegate calls"""
    self.assertRoutes((
      ('/level2/level3/func_on_level2', http.NotFound),
      ('/level2/level3/posts/func_on_level2', http.NotFound),
      ('/level2/level3/posts/', http.NotFound),
    ))
  
  def test4_delegating(self):
    """Access inherited leafs which do delegate calls"""
    self.assertRoutes((
      ('/level2/delegating_func_on_root', '/delegating_func_on_root'),
      ('/level2/level3/delegating_func_on_root', '/delegating_func_on_root'),
      ('/level2/level3/posts/delegating_func_on_root', '/delegating_func_on_root'),
    ))
  
  def test5_renamed(self):
    """Access renamed nodes, for example by @expose(name=)"""
    self.assertRoutes((
      ('/level2/foo-bar', '/level2/foo-bar'),
      ('/level2/foo_bar', http.NotFound),
      ('/level2/level-3-b/func_on_level3B', '/level2/level-3-b/func_on_level3B'),
      ('/level2/level3B/func_on_level3B', http.NotFound),
    ))
  
  def test6_hidden(self):
    self.assertRoutes((
      ('/level2/level3/hidden_method_on_level3', http.NotFound),
    ))
  
  def test7_protected_on_Controller(self):
    self.assertRoutes((
      ('/controller_name', http.NotFound),
      ('/controller_name', http.NotFound),
      ('/controller_name', http.NotFound),
    ))
  
  def test8_special_builtins(self):
    # These should succeed
    special_names = Controller.special_methods().keys()
    not_found_tests = []
    for name in special_names:
      not_found_tests.append(('/level2/%s' % name, http.NotFound))
      dest, args, params = self.router(URL('/%s' % name), [], {})
      self.assertTrue(dest())
    # These should fail
    self.assertRoutes(not_found_tests)
  
  def assertRoutes(self, urls, router=None):
    if router is None:
      r = self.router
    else:
      r = router
    for url, expected_return in urls:
      url = URL(url)
      if echo:
        print 'Calling \'%s\' expected to return %r' % (url, expected_return)
      dest, args, params = r(url, [], {})
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
          returned = dest()
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
