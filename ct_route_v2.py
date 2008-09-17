#!/usr/bin/env python
# encoding: utf-8
import sys, os
from types import *
from smisk.core import URL
from smisk.mvc.control import Controller

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


def strip_filename_extension(fn):
  try:
    return fn[:fn.rindex('.')]
  except:
    return fn

class Router(object):
  def __init__(self):
    self.cache = {}
  
  def tokenize_path(self, path):
    tokens = []
    for tok in path.split('/'):
      tok = URL.decode(tok)
      if len(tok):
        tokens.append(tok)
    if tokens:
      tokens[-1] = strip_filename_extension(tokens[-1])
    return tokens
  
  def __call__(self, path):
    raw_path = path.strip('/').lower()
    
    # Cached?
    if raw_path in self.cache:
      return self.cache[raw_path]
    
    # Tokenize path
    path = self.tokenize_path(path)
    node = root
    
    # Special case -- empty path means root.__call__
    if not path:
      try:
        node = node().__call__
        self.cache[raw_path] = node
        return node
      except AttributeError:
        return
    
    # Traverse tree
    for part in path:
      found = None
      
      # 1. Search subclasses first
      for cls in node.__subclasses__():
        if cls.__name__.lower() == part:
          found = cls
          break
      if found is not None:
        node = found
        #print '>> matched %s to class %s' % (part, node)
        continue
      
      # 2. Search methods
      # Aquire instance
      if type(node) is type:
        node = node()
      for k,v in node.__dict__.items():
        if k.lower() == part:
          found = v
          break
      if found is not None:
        node = found
        node_type = type(node)
        if node_type is MethodType or node_type is FunctionType:
          #print '>> matched function/method -- LEAF'
          break
        # else we continue...
      else:
        #print '>> 404 Not Found -- url part not found'
        self.cache[raw_path] = None
        return
    
    # Did we hit a class/type at the end? If so, get its instance.
    if type(node) is type:
      #print '>> hit type %s at end -- converting' % node
      try:
        node = node().__call__
      except AttributeError:
        node = None
    
    self.cache[raw_path] = node
    return node
    
  

r = Router()
print r('/')
print r('/func_on_root')
print r('/level2')
print r('/level2/func_on_level2')
print r('/level2/nothing/here')
print r('/level2/level3')
print r('/level3')
print r('/level2/level3/func_on_level3')

from smisk.util.timing import Timer
t = Timer(True)
for x in xrange(100000):
  m = r('/')
  m = r('/func_on_root')
  m = r('/level2')
  m = r('/level2/func_on_level2')
  m = r('/level2/nothing/here')
  m = r('/level2/level3')
  m = r('/level3')
  m = r('/level2/level3/func_on_level3')
print t.finish()