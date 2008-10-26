# encoding: utf-8
'''MVC test matter
'''
from smisk.mvc import *

# A controller tree

class root(Controller):
  def func_on_root(self): return '/func_on_root'
  @expose(delegates=True)
  def delegating_func_on_root(self): return '/delegating_func_on_root'
  def __call__(self, *va, **kw): return '/'

class level2(root):
  def __call__(self): return '/level2'
  #func_on_level2 = root
  def func_on_level2(self, *va, **kw): return '/level2/func_on_level2'
  def level3(self):
    '''never reached from outside, because it's shadowed by subclass level3.
    However, it can still be reaced internally, through for example
    control.path_to().
    '''
    return 'shadowed'
  @expose('foo-bar')
  def foo_bar(self): return '/level2/foo-bar'

class level3(level2):
  def __call__(self): return '/level2/level3'
  @hide
  def hidden_method_on_level3(self): pass
  def func_on_level3(self, *va): return '/level2/level3/func_on_level3'
  def func_on_level3_wonlykwa(self, **kva): return '/level2/level3/func_on_level3_wonlykwa'

class level3B(level2):
  slug = 'level-3-b'
  def func_on_level3B(self): return '/level2/level-3-b/func_on_level3B'

class PostsController(level3):
  def list(self, *va, **kw): return '/level2/level3/posts/list'


# For testing method_origin and alike:

class Animal(object):
  def name(self): pass

class Fish(Animal):
  def color(self): pass

class Bass(Fish):
  def eats(self): pass
  def sleeps(self): pass

class SpanishBass(Bass):
  def on_fiesta(self): pass
  def sleeps(self): pass

class EnglishBass(Bass):
  def on_fiesta(self): return False
  def cheese(self): pass
