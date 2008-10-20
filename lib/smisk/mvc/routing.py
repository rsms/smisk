#!/usr/bin/env python
# encoding: utf-8
'''URL-to-function routing.
'''
import sys, re, logging
from types import *
from smisk.core import URL
from smisk.util import None2, tokenize_path, wrap_exc_in_callable, introspect, Undefined
import http, control

log = logging.getLogger(__name__)

def _prep_path(path):
  return path.rstrip('/').lower()

def _node_name(node, fallback):
  n = getattr(node, 'slug', None)
  if n is None:
    return fallback
  return n

class Destination(object):
  '''A callable destination.
  '''
  
  action = None
  ''':type: callable
  '''
  
  def __init__(self, action):
    self.action = introspect.ensure_va_kwa(action)
    self.formats = None
    try:
      self.formats = self.action.formats
    except AttributeError:
      pass
  
  def __call__(self, *args, **params):
    '''Call action
    '''
    try:
      return self.action(*args, **params)
    except TypeError:
      typ, val, tb = sys.exc_info()
      # Get the last frame
      while 1:
        nxt = tb.tb_next
        if nxt:
          tb = nxt
        else:
          break
      # If the exception occured in this very method, we know
      # it's because required parameters are missing.
      if tb.tb_frame.f_code == self.__call__.im_func.func_code:
        info = introspect.callable_info(self.action)
        args = []
        for k,v in info['args']:
          if v is Undefined:
            args.append(k)
        args = ', '.join(args)
        raise http.BadRequest('%s requires parameters: %s' % (self.uri, args))
      # TypeError from another source are delegated
      raise
      
  
  @property
  def path(self):
    '''Canonical exposed path.
    
    :rtype: list
    '''
    return control.path_to(self.action)
  
  @property
  def uri(self):
    '''Canonical exposed URI.
    
    :rtype: string
    '''
    return control.uri_for(self.action)
  
  @property
  def template_path(self):
    '''Template path.
    
    :rtype: list
    '''
    return control.template_for(self.action)
  
  def __str__(self):
    if self.path:
      return '/'+'/'.join(self.path)
    else:
      return self.__repr__()
  
  def __repr__(self):
    return '%s(action=%r, uri=%r)' \
      % (self.__class__.__name__, self.action, self.uri)
  

class Filter(object):
  def __init__(self, pattern, destination_path, match_on_full_url=False, **params):
    self.pattern = pattern
    self.destination_path = _prep_path(destination_path)
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
  
  def __repr__(self):
    return '<%s.%s(%r, %r) @0x%x>' %\
      (self.__module__, self.__class__.__name__, \
      self.pattern.pattern, self.destination_path, id(self))
  


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
      
      def show(self, name, *args, **params):
        return {'employee': Employee.get_by(name=name)}
      
      class edit(employees):
        def save(self, employee_id, *args, **params):
          Employee.get_by(id=employee_id).save_or_update(**params)
  
  
  Now, this list shows what URIs would map to what begin called:
  
  .. python::
    /                         => root().__call__()
    /employees                => employees().__call__()
    /employees/               => employees().__call__()
    /employees/show           => employees().show()
    /employees/show?name=foo  => employees().show(name='foo')
    /employees/show/123       => None
    /employees/edit/save      => employees.edit().save()
  
  See source of ``smisk.test.routing`` for more examples.
  '''
  
  def __init__(self):
    self.cache = {}
    self.filters = []
  
  def filter(self, regexp, destination_path, regexp_flags=re.I, match_on_full_url=False, **params):
    '''Explicitly map an action to paths or urls matching regular expression `regexp`.
    
    Excessive keyword arguments are saved and later included in every call to
    action taking this route.
    
    :param regexp:            Pattern
    :type  regexp:            re.RegExp
    :param destination_path:  Path to action, expressed in internal canonical form.
                              i.e. "/controller/action".
    :type  destination_path:  string
    :param regexp_flags:      Defaults to ``re.I`` (case-insensitive)
    :type  regexp_flags:      int
    :param match_on_full_url: Where there or not to perform matches on complete
                              URL (i.e. "https://foo.tld/bar?question=2").
                              Defauts to False (i.e.matches on path only. "/bar")
    :type  match_on_full_url: bool
    :rtype: None'''
    if not isinstance(regexp_flags, int):
      regexp_flags = 0
    pattern = re.compile(regexp, regexp_flags)
    filter = Filter(pattern, destination_path, match_on_full_url, **params)
    self.filters.append(filter)
    return filter
  
  
  def __call__(self, url, args, params):
    '''
    Find destination for route `url`.
    
    :param url: The URL to consider
    :type  url: smisk.core.URL
    :return: ('Destionation' ``dest``, list ``args``, dict ``params``).
             ``dest`` might be none if no route to destination.
    :rtype: tuple
    '''
    # Explicit mapping? (never cached)
    for filter in self.filters:
      dargs, dparams = filter.match(url)
      if dargs is not None:
        dargs.extend(args)
        dparams.update(params)
        return self._resolve_cached(filter.destination_path), dargs, dparams
    
    return self._resolve_cached(_prep_path(url.path)), args, params
  
  def _resolve_cached(self, raw_path):
    try:
      return self.cache[raw_path]
    except KeyError:
      dest = Destination(self._resolve(raw_path))
      self.cache[raw_path] = dest
      return dest
  
  def _resolve(self, raw_path):
    log.debug('Resolving %s', raw_path)
    
    # Tokenize path
    path = tokenize_path(raw_path)
    node = control.root_controller()
    
    # Check root
    if node is None:
      return wrap_exc_in_callable(http.ControllerNotFound('No root controller exists'))
    
    # Special case: empty path == root.__call__
    if not path:
      try:
        node = node().__call__
        log.debug('Found destination: %s', node)
        return node
      except AttributeError:
        return wrap_exc_in_callable(http.MethodNotFound('/'))
    
    # Traverse tree
    for part in path:
      found = None
      
      # 1. Search subclasses first
      for cls in node.__subclasses__():
        if _node_name(cls, cls.controller_name()) == part:
          if getattr(cls, 'hidden', False):
            continue
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
        if _node_name(v, k.lower()) == part:
          if getattr(v, 'hidden', False):
            continue
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
        return wrap_exc_in_callable(http.MethodNotFound('/'.join(path)))
    
    # Did we hit a class/type at the end? If so, get its instance.
    if type(node) is type:
      #print '>> hit type %s at end -- converting' % node
      try:
        node = node().__call__
      except AttributeError:
        # Uncallable leaf
        node = None
    
    # Not callable?
    if node is None or not callable(node):
      return wrap_exc_in_callable(http.MethodNotFound('/'.join(path)))
    
    log.debug('Found destination: %s', node)
    return node
  

if __name__ == '__main__':
  from smisk.test.routing import test
  test()
