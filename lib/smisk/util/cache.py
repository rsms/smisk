# encoding: utf-8
'''Cache-related utilities.
'''
from types import *
import sys, os

__all__ = ['callable_cache_key', 'app_shared_key']

def callable_cache_key(node):
  '''Calculate key unique enought to be used for caching callables.
  '''
  if not isinstance(node, (MethodType, FunctionType)):
    return hash(node.__call__)^hash(node)
  elif isinstance(node, MethodType):
    return hash(node)^hash(node.im_class)
  return node

def app_shared_key():
  fn = sys.modules['__main__'].__file__
  h = hash(fn)
  if h < 0:
    h = 'a%lx' % -h
  else:
    h = 'b%lx' % h
  name = os.path.splitext(os.path.basename(fn))[0]
  if name == '__init__':
    name = os.path.basename(os.path.dirname(os.path.abspath(fn)))
  return '%s_%s' % (name, h)
