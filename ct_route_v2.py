#!/usr/bin/env python
# encoding: utf-8
import sys, os, re
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


None2 = (None, None)

def strip_filename_extension(fn):
  try:
    return fn[:fn.rindex('.')]
  except:
    return fn

###############################################################################


class Destination(object):
  # These should not be modified directly from outside of a router,
  # since routers might cache instances of Destination.
  action = None
  ''':type: function'''
  
  path = None
  '''
  Canonical internal path.
  
  some.module.controllers.posts.list.__call__()
  Is represented as, if "posts" parent class is the same as Router.root_controller:
  ['posts', 'list', '__call__']
  But might be called from any external URL:
  /posts/list
  /posts/list.json
  /some/other/url
  
  :type: list
  '''
  
  def __init__(self, action):
    self.action = action
    self.path = []
  
  def __call__(self, *args, **kwargs):
    return self.action(*args, **kwargs)
  
  def __str__(self):
    if self.path:
      return '/'.join(self.path)
    else:
      return self.__repr__()
  
  def __repr__(self):
    return '%s(action=%s, path=%s)' \
      % (self.__class__.__name__, repr(self.action), repr(self.path))


class RegExpDestination(Destination):
  def __init__(self, regexp, action, match_on_full_url=False, **params):
    super(RegExpDestination, self).__init__(action)
    self.pattern = regexp
    self.match_on_full_url = match_on_full_url
    self.params = params
  
  def match(self, url):
    if self.match_on_full_url:
      m = self.pattern.match(url)
    else:
      m = self.pattern.match(url.path)
    if m is not None:
      if self.params:
        params = self.params.copy()
        params.extend(m.groupdict())
      else:
        params = m.groupdict()
      return list(m.groups()), params
    return None2
  


class Router(object):
  def __init__(self):
    self.cache = {}
    self.mappings = []
  
  def map(self, regexp, action, match_on_full_url=False, **params):
    '''Explicitly map an action to paths or urls matching regexp'''
    self.mappings.append(RegExpDestination(re.compile(regexp), 
                                           action, match_on_full_url, 
                                           **params))
  
  def tokenize_path(self, path):
    tokens = []
    for tok in path.split('/'):
      tok = URL.decode(tok)
      if len(tok):
        tokens.append(tok)
    if tokens:
      tokens[-1] = strip_filename_extension(tokens[-1])
    return tokens
  
  def __call__(self, url, args, params):
    raw_url = str(url).rstrip('/').lower()
    
    # Cached?
    if raw_url in self.cache:
      dest = self.cache[raw_url]
      if dest.__class__ is RegExpDestination:
        dargs, dparams = dest.match(url)
        dargs.extend(args)
        dparams.update(params)
        return dest, dargs, dparams
      return dest, args, params
    
    # Explicit mapping?
    for dest in self.mappings:
      dargs, dparams = dest.match(url)
      if dargs is not None:
        self.cache[raw_url] = dest
        dargs.extend(args)
        dparams.update(params)
        return dest, dargs, dparams
    
    # Tokenize path
    path = self.tokenize_path(url.path)
    node = root
    
    # Special case -- empty path means root.__call__
    if not path:
      try:
        node = node().__call__
        dest = Destination(node)
        self.cache[raw_url] = dest
        return dest, args, params
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
        self.cache[raw_url] = None
        return
    
    # Did we hit a class/type at the end? If so, get its instance.
    if type(node) is type:
      #print '>> hit type %s at end -- converting' % node
      try:
        node = node().__call__
      except AttributeError:
        #print '>> 404 Not Found -- uncallable leaf'
        self.cache[raw_url] = None
        return
    
    dest = Destination(node)
    self.cache[raw_url] = dest
    return dest, args, params
  

r = Router()
r.map(r'^/user', level2().func_on_level2)
urls = [
  '/',
  '/func_on_root',
  '/level2',
  '/level2/func_on_level2',
  '/level2/nothing/here',
  '/level2/level3',
  '/level2/level3/__call__',
  '/user/rasmus',
  '/user/rasmus/photos',
  '/level3',
  '/level2/level3/func_on_level3',
]
for url in urls:
  url = URL(url)
  print url, '==>\n', r(url, [], {}), '\n'

sys.exit(0)

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