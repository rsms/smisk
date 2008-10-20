#!/usr/bin/env python
# encoding: utf-8
from smisk.test import *
from smisk.util import *
from smisk.mvc.control import *

from test_matter import *

class misc_tests(TestCase):
  def test1_root_controller(self):
    self.assertEquals(root_controller(), root)
  
  def test2_controllers(self):
    self.assertContains(controllers(), (
      root(), level2(), level3(), level3B(), PostsController()
    ))
  
  def test3_method_origin(self):
    o = SpanishBass()
    self.assertEquals(method_origin(o.name), Animal)
    self.assertEquals(method_origin(o.color), Fish)
    self.assertEquals(method_origin(o.eats), Bass)
    self.assertEquals(method_origin(o.on_fiesta), SpanishBass)
    self.assertEquals(method_origin(o.sleeps), SpanishBass)
    o = EnglishBass()
    self.assertEquals(method_origin(o.cheese), EnglishBass)
    self.assertEquals(method_origin(o.on_fiesta), EnglishBass)
  
  def test4_leaf_visibility(self):
    # Visible
    self.assertTrue(leaf_is_visible(root))
    self.assertTrue(leaf_is_visible(root.__call__))
    self.assertTrue(leaf_is_visible(root.func_on_root))
    self.assertTrue(leaf_is_visible(root.delegating_func_on_root))
    self.assertTrue(leaf_is_visible(level2))
    self.assertTrue(leaf_is_visible(level2.__call__))
    self.assertTrue(leaf_is_visible(level2.func_on_level2))
    self.assertTrue(leaf_is_visible(level2.level3)) # maybe should be False
    self.assertTrue(leaf_is_visible(level3))
    self.assertTrue(leaf_is_visible(level3.__call__))
    self.assertTrue(leaf_is_visible(level3.func_on_level3))
    self.assertTrue(leaf_is_visible(level2.delegating_func_on_root))
    self.assertTrue(leaf_is_visible(level3.delegating_func_on_root))
    self.assertTrue(leaf_is_visible(PostsController.delegating_func_on_root))
    self.assertTrue(leaf_is_visible(level2.foo_bar))
    # Invisible
    self.assertFalse(leaf_is_visible(level2.func_on_root))
    self.assertFalse(leaf_is_visible(level3.func_on_level2))
    self.assertFalse(leaf_is_visible(level3B))
    self.assertFalse(leaf_is_visible(level3B.__call__))
    self.assertFalse(leaf_is_visible(level3.hidden_method_on_level3))
  
  def test5_controller_name(self):
    self.assertEquals(root.controller_name(), u'root')
    self.assertEquals(level2.controller_name(), u'level2')
    self.assertEquals(level3.controller_name(), u'level3')
    self.assertEquals(level3B.controller_name(), u'level-3-b')
    self.assertEquals(PostsController.controller_name(), u'posts')

class node_name_tests(TestCase):
  def test1_basic(self):
    self.assertEquals(node_name(root), u'')
    self.assertEquals(node_name(root.__call__), u'')
    self.assertEquals(node_name(root.func_on_root), u'func_on_root')
    self.assertEquals(node_name(root.delegating_func_on_root), u'delegating_func_on_root')
    self.assertEquals(node_name(level2), u'level2')
    self.assertEquals(node_name(level2.__call__), u'level2')
    self.assertEquals(node_name(level2.func_on_level2), u'func_on_level2')
    self.assertEquals(node_name(level2.level3), u'level3') # shadowed with purpose
    self.assertEquals(node_name(level3), u'level3')
    self.assertEquals(node_name(level3.__call__), u'level3')
    self.assertEquals(node_name(level3.func_on_level3), u'func_on_level3')
  
  def test2_non_delegating(self):
    self.assertEquals(node_name(level2.func_on_root), None)
    self.assertEquals(node_name(level3.func_on_level2), None)
    self.assertEquals(node_name(level3B), None)
    self.assertEquals(node_name(level3B.__call__), None)
  
  def test3_delegating(self):
    self.assertEquals(node_name(level2.delegating_func_on_root), u'delegating_func_on_root')
    self.assertEquals(node_name(level3.delegating_func_on_root), u'delegating_func_on_root')
    self.assertEquals(node_name(PostsController.delegating_func_on_root),\
      u'delegating_func_on_root')
  
  def test4_renamed(self):
    self.assertEquals(node_name(level2.foo_bar), u'foo-bar')
    self.assertNotEquals(node_name(level2.foo_bar), u'foo_bar')
  
  def test5_hidden(self):
    self.assertEquals(node_name(level3.hidden_method_on_level3), None)
  

class path_to_tests(TestCase):
  def test1_basic(self):
    self.assertEquals(path_to(root), \
      [])
    self.assertEquals(path_to(root.__call__), \
      [])
    self.assertEquals(path_to(root.func_on_root), \
      [u'func_on_root'])
    self.assertEquals(path_to(root.delegating_func_on_root),\
      [u'delegating_func_on_root'])
    self.assertEquals(path_to(level2), \
      [u'level2'])
    self.assertEquals(path_to(level2.__call__), \
      [u'level2'])
    self.assertEquals(path_to(level2.func_on_level2),\
      [u'level2',u'func_on_level2'])
    self.assertEquals(path_to(level2.level3),\
      [u'level2',u'level3']) # shadowed with purpose
    self.assertEquals(path_to(level3),\
      [u'level2',u'level3'])
    self.assertEquals(path_to(level3.__call__),\
      [u'level2',u'level3'])
    self.assertEquals(path_to(level3.func_on_level3),\
      [u'level2',u'level3',u'func_on_level3'])
  
  def test2_non_delegating(self):
    self.assertEquals(path_to(level2.func_on_root), None)
    self.assertEquals(path_to(level3.func_on_level2), None)
    self.assertEquals(path_to(level3B), None)
    self.assertEquals(path_to(level3B.__call__), None)
  
  def test3_delegating(self):
    self.assertEquals(path_to(level2.delegating_func_on_root),\
      [u'level2',u'delegating_func_on_root'])
    self.assertEquals(path_to(level3.delegating_func_on_root),\
      [u'level2',u'level3',u'delegating_func_on_root'])
    self.assertEquals(path_to(PostsController.delegating_func_on_root),\
      [u'level2',u'level3',u'posts',u'delegating_func_on_root'])
  
  def test4_renamed(self):
    self.assertEquals(path_to(level2.foo_bar), [u'level2',u'foo-bar'])
    self.assertNotEquals(path_to(level2.foo_bar), [u'level2',u'foo_bar'])
  
  def test5_hidden(self):
    self.assertEquals(path_to(level3.hidden_method_on_level3), None)
  

class uri_for_tests(TestCase):
  def test1_basic(self):
    self.assertEquals(uri_for(root), \
      u'/')
    self.assertEquals(uri_for(root.__call__), \
      u'/')
    self.assertEquals(uri_for(root.func_on_root), \
      u'/func_on_root')
    self.assertEquals(uri_for(root.delegating_func_on_root),\
      u'/delegating_func_on_root')
    self.assertEquals(uri_for(level2), \
      u'/level2/')
    self.assertEquals(uri_for(level2.__call__), \
      u'/level2/')
    self.assertEquals(uri_for(level2.func_on_level2),\
      u'/level2/func_on_level2')
    self.assertEquals(uri_for(level2.level3),\
      u'/level2/level3') # shadowed with purpose
    self.assertEquals(uri_for(level3),\
      u'/level2/level3/')
    self.assertEquals(uri_for(level3.__call__),\
      u'/level2/level3/')
    self.assertEquals(uri_for(level3.func_on_level3),\
      u'/level2/level3/func_on_level3')
  
  def test2_non_delegating(self):
    self.assertEquals(uri_for(level2.func_on_root), None)
    self.assertEquals(uri_for(level3.func_on_level2), None)
    self.assertEquals(uri_for(level3B), None)
    self.assertEquals(uri_for(level3B.__call__), None)
  
  def test3_delegating(self):
    self.assertEquals(uri_for(level2.delegating_func_on_root),\
      u'/level2/delegating_func_on_root')
    self.assertEquals(uri_for(level3.delegating_func_on_root),\
      u'/level2/level3/delegating_func_on_root')
    self.assertEquals(uri_for(PostsController.delegating_func_on_root),\
      u'/level2/level3/posts/delegating_func_on_root')
  
  def test4_renamed(self):
    self.assertEquals(uri_for(level2.foo_bar), u'/level2/foo-bar')
    self.assertNotEquals(uri_for(level2.foo_bar), u'/level2/foo_bar')
  
  def test5_hidden(self):
    self.assertEquals(uri_for(level3.hidden_method_on_level3), None)
  

class template_for_tests(TestCase):
  def test1_basic(self):
    self.assertEquals(template_for(root), \
      [u'__call__'])
    self.assertEquals(template_for(root.__call__), \
      [u'__call__'])
    self.assertEquals(template_for(root.func_on_root), \
      [u'func_on_root'])
    self.assertEquals(template_for(root.delegating_func_on_root),\
      [u'delegating_func_on_root'])
    self.assertEquals(template_for(level2), \
      [u'level2',u'__call__'])
    self.assertEquals(template_for(level2.__call__), \
      [u'level2',u'__call__'])
    self.assertEquals(template_for(level2.func_on_level2),\
      [u'level2',u'func_on_level2'])
    self.assertEquals(template_for(level2.level3),\
      [u'level2',u'level3']) # shadowed with purpose
    self.assertEquals(template_for(level3),\
      [u'level2',u'level3',u'__call__'])
    self.assertEquals(template_for(level3.__call__),\
      [u'level2',u'level3',u'__call__'])
    self.assertEquals(template_for(level3.func_on_level3),\
      [u'level2',u'level3',u'func_on_level3'])
  
  def test2_non_delegating(self):
    self.assertEquals(template_for(level2.func_on_root), None)
    self.assertEquals(template_for(level3.func_on_level2), None)
    self.assertEquals(template_for(level3B), None)
    self.assertEquals(template_for(level3B.__call__), None)
  
  def test3_delegating(self):
    self.assertEquals(template_for(level2.delegating_func_on_root),\
      [u'level2',u'delegating_func_on_root'])
    self.assertEquals(template_for(level3.delegating_func_on_root),\
      [u'level2',u'level3',u'delegating_func_on_root'])
    self.assertEquals(template_for(PostsController.delegating_func_on_root),\
      [u'level2',u'level3',u'posts',u'delegating_func_on_root'])
  
  def test4_renamed(self):
    self.assertEquals(template_for(level2.foo_bar), [u'level2',u'foo-bar'])
    self.assertNotEquals(template_for(level2.foo_bar), [u'level2',u'foo_bar'])
  
  def test5_hidden(self):
    self.assertEquals(template_for(level3.hidden_method_on_level3), None)
  


def suite():
  return unittest.TestSuite([
    unittest.makeSuite(misc_tests),
    unittest.makeSuite(node_name_tests),
    unittest.makeSuite(path_to_tests),
    unittest.makeSuite(uri_for_tests),
    unittest.makeSuite(template_for_tests),
  ])

def test():
  runner = unittest.TextTestRunner()
  return runner.run(suite())

if __name__ == "__main__":
  test()
