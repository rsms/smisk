#!/usr/bin/env python
# encoding: utf-8
import unittest
from smisk.mvc.routing import *

# Test matter
class root(Controller):
  def func_on_root(self): pass
  def __call__(self): pass

class level2(root):
  def __call__(self): pass
  #func_on_level2 = root
  def func_on_level2(self): pass
  def level3(self): pass

class level3(level2):
  def __call__(self): pass
  def func_on_level3(self): pass

class PostsController(level3):
  def list(self): pass


class RoutingTests(unittest.TestCase):
  def test1(self):
    r = Router()
    r.map(r'^/user/(?P<user>[^/]+)', level2().func_on_level2)
    r.map(r'^/archive/(\d{4})/(\d{2})/(\d{2})', level3().__call__, regexp_flags=0)
    urls = [
      ('/', root().__call__),
      ('/func_on_root', root().func_on_root),
      ('/level2', level2().__call__),
      ('/level2/func_on_level2', level2().func_on_level2),
      ('/level2/nothing/here', None),
      ('/level2/level3', level3().__call__),
      ('/level2/LEVEL3', level3().__call__),
      ('/level2/level3/__call__', None),
      ('/level3', None),
      ('/level2/level3/func_on_level3', level3().func_on_level3),
      ('/user/rasmus/photos', level2().func_on_level2),
      ('/user/rasmus', level2().func_on_level2),
      ('/USER/rasmus', level2().func_on_level2),
      ('/user', None),
      ('/archive/2008/01/15', level3().__call__),
      ('/ARCHIVE/2008/01/15/foo', None),
      ('/level2/level3/posts/list', PostsController().list),
      ('/level2/level3/posts/', PostsController().__call__),
    ]
    do_print = False
    if __name__ == '__main__':
      do_print = True
      print 'Printing out loud because __name__ == __main__'
    for url,func in urls:
      url = URL(url)
      dest, args, params = r(url, [], {})
      if dest is not None:
        dest = dest.action
      if do_print:
        print '"%s" => %s (%s, %s)' % (url, dest, args, params)
      assert dest == func, '"%s" => %s' % (url, dest)
  

def suite():
  return unittest.TestSuite([
    unittest.makeSuite(RoutingTests),
  ])

def test():
  runner = unittest.TextTestRunner()
  return runner.run(suite())

if __name__ == "__main__":
  test()
