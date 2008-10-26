# encoding: utf-8
'''Cache-related utilities.
'''
from types import *

__all__ = ['callable_cache_key']

def callable_cache_key(node):
  '''Calculate key unique enought to be used for caching callables.
  '''
  if not isinstance(node, (MethodType, FunctionType)):
    return hash(node.__call__)^hash(node)
  elif isinstance(node, MethodType):
    return hash(node)^hash(node.im_class)
  return node
