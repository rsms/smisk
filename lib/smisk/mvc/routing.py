#!/usr/bin/env python
# encoding: utf-8
'''
URL-to-function routing.
'''
import re, logging
from types import *
from smisk.core import URL
from smisk.util import None2, tokenize_path, wrap_exc_in_callable
import http, control

log = logging.getLogger(__name__)

class Destination(object):
  '''A callable destination.'''
  
  action = None
  ''':type: callable'''
  
  def __init__(self, action):
    self.action = action
  
  def __call__(self, *args, **params):
    '''Call action'''
    return self.action(*args, **params)
  
  @property
  def path(self):
    '''
    Canonical path.
    
    :type: list
    '''
    return control.path_to(self.action)
  
  def __str__(self):
    if self.path:
      return '/'.join(self.path)
    else:
      return self.__repr__()
  
  def __repr__(self):
    return '%s(action=%r, path=%r)' \
      % (self.__class__.__name__, self.action, self.path)
  


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
        params.update(m.groupdict())
      else:
        params = m.groupdict()
      return list(m.groups()), params
    return None2
  


class Router(object):
  '''
  Default router handling both RegExp mappings and class tree mappings.
  
  Consider the following tree of controllers:
  
  .. python::
    class root(Controller):
      def __call__(self, *args, **params):
        return 'Welcome!'
    
    class employees(root):
      def __call__(self, *args, **params):
        return {'employees': Employee.query.all()}
      
      def show(self, employee_id, *args, **params):
        return {'employee': Employee.get_by(id=employee_id)}
      
      class edit(employees):
        def __call__(self, employee_id, *args, **params):
          return employees.show(self, employee_id)
        
        def save(self, employee_id, *args, **params):
          Employee.get_by(id=employee_id).save_or_update(**params)
  
  
  Now, this list shows what URIs would map to what begin called:
  
  .. python::
    /                             => root().__call__()
    /employees                    => employees().__call__()
    /employees/                   => employees().__call__()
    /employees/show               => employees().show()
    /employees/show/123           => employees().show(123)
    /employees/show/123/456       => employees().show(123, 456)
    /employees/show/123?other=456 => employees().show(123, other=456)
    /employees/edit/123           => employees.edit().__call__(123)
    /employees/edit/save/123      => employees.edit().save(123)
  
  See `smisk.test.routing` for more examples.
  '''
  
  def __init__(self):
    self.cache = {}
    self.mappings = []
  
  def map(self, regexp, action, regexp_flags=re.I, match_on_full_url=False, **params):
    '''Explicitly map an action to paths or urls matching regular expression `regexp`.
    
    Excessive keyword arguments are saved and later included in every call to
    action taking this route.
    
    :param regexp:
    :type  regexp: re.RegExp
    :param action:
    :type  action: callable
    :param regexp_flags: Defaults to ``re.I`` (case-insensitive)
    :type  regexp_flags: int
    :param match_on_full_url: Where there or not to perform matches on complete
      URL (i.e. "https://foo.tld/bar?question=2"). Defauts to False (i.e. 
      matches on path only. "/bar")
    :type  match_on_full_url: bool
    :rtype: None'''
    if not isinstance(regexp_flags, int):
      regexp_flags = 0
    self.mappings.append(RegExpDestination(re.compile(regexp, regexp_flags), 
                                           action, match_on_full_url, 
                                           **params))
  
  def __call__(self, url, args, params):
    '''
    Find destination for route `url`.
    
    :param url: The URL to consider
    :type  url: smisk.core.URL
    :return: Destionation dest, list args, dict params.
             `dest` might be none if no route to destination.
    :rtype: tuple
    '''
    raw_url = str(url).rstrip('/').lower()
    
    # Cached?
    if raw_url in self.cache:
      dest = self.cache[raw_url]
      return dest, args, params
    
    log.debug('Resolving %s', url)
    
    # Explicit mapping? (never cached)
    for dest in self.mappings:
      dargs, dparams = dest.match(url)
      if dargs is not None:
        dargs.extend(args)
        dparams.update(params)
        return dest, dargs, dparams
    
    # Tokenize path
    path = tokenize_path(url.path)
    node = control.root_controller()
    
    # Check root
    if node is None:
      e = http.ControllerNotFound('No root controller could be found')
      self.cache[raw_url] = wrap_exc_in_callable(e)
      raise e
    
    # Special case: empty path == root.__call__
    if not path:
      try:
        node = node().__call__
        log.debug('Found destination: %s', node)
        dest = Destination(node)
        self.cache[raw_url] = dest
        return dest, args, params
      except AttributeError:
        e = http.MethodNotFound('/')
        self.cache[raw_url] = wrap_exc_in_callable(e)
        raise e
    
    # Traverse tree
    for part in path:
      found = None
      
      # 1. Search subclasses first
      for cls in node.__subclasses__():
        if cls.controller_name() == part:
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
        # Not found
        e = http.MethodNotFound('/'.join(path))
        self.cache[raw_url] = wrap_exc_in_callable(e)
        raise e
    
    # Did we hit a class/type at the end? If so, get its instance.
    if type(node) is type:
      #print '>> hit type %s at end -- converting' % node
      try:
        node = node().__call__
      except AttributeError:
        # Uncallable leaf
        e = http.MethodNotFound('/'.join(path))
        self.cache[raw_url] = wrap_exc_in_callable(e)
        raise e
    
    log.debug('Found destination: %s', node)
    dest = Destination(node)
    self.cache[raw_url] = dest
    return dest, args, params
  

if __name__ == '__main__':
  from smisk.test.routing import test
  test()
