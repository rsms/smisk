#!/usr/bin/env python
# encoding: utf-8
'''URL-to-function routing.
'''
import sys, re, logging, new
from smisk.mvc import http
from smisk.mvc import control
from smisk.core import URL
from smisk.config import config
from smisk.util.type import *
from smisk.util.python import wrap_exc_in_callable
from smisk.util.string import tokenize_path
from smisk.util.introspect import introspect

__all__ = ['Destination', 'Filter', 'Router']
log = logging.getLogger(__name__)

def _prep_path(path):
  return unicode(path).rstrip(u'/').lower()

def _node_name(node, fallback):
  n = getattr(node, 'slug', None)
  if n is None:
    return fallback
  return n

def _find_canonical_leaf(leaf, rel_im_leaf):
  canonical_leaf = leaf
  try:
    while 1:
      canonical_leaf = canonical_leaf.parent_leaf
  except AttributeError:
    pass
  if isinstance(canonical_leaf, FunctionType) \
  and canonical_leaf.__name__ not in ('va_kwa_wrapper', 'exc_wrapper'):
    # In this case, the leaf has been decorated and thus need to be bound into
    # a proper instance method.
    canonical_leaf = new.instancemethod(canonical_leaf, rel_im_leaf.im_self, rel_im_leaf.im_class)
  return canonical_leaf


class Destination(object):
  '''A callable destination.
  '''
  
  leaf = None
  ''':type: callable
  '''
  
  def __init__(self, leaf):
    self.leaf = leaf
    self.formats = None
    try:
      self.formats = self.leaf.formats
    except AttributeError:
      pass
  
  def _call_leaf(self, *args, **params):
    return self.leaf(*args, **params)
  
  def __call__(self, *args, **params):
    '''Call leaf
    '''
    try:
      return self._call_leaf(*args, **params)
    except TypeError, e:
      desc = e.args[0]
      
      # Find out if the problem was caused in self._call_leaf or originates someplace else
      tb = sys.exc_info()[2]
      if not tb:
        raise
      while 1:
        if tb.tb_next:
          tb = tb.tb_next
        else:
          break
      if tb.tb_lineno != self._call_leaf.im_func.func_code.co_firstlineno+1:
        raise
      
      GOT_MUL = ' got multiple values for keyword argument '
      
      def req_args():
        info = introspect.callable_info(self.leaf)
        args = []
        for k,v in info['args']:
          if v is Undefined:
            args.append(k)
        return ', '.join(args)
      
      if (desc.find(' takes at least ') > 0 and desc.find(' arguments ') > 0) or (desc.find(' takes exactly ') > 0):
        log.debug('TypeError', exc_info=1)
        raise http.BadRequest('Missing required parameters: %r (Received %r, %r)' % \
          (req_args(), params, args))
      else:
        p = desc.find(GOT_MUL)
        if p > 0:
          raise http.BadRequest('%s got multiple values for keyword argument %s'\
            ' -- received args %r and params %r' % \
            (self.uri, desc[p+len(GOT_MUL):], args, params))
      raise
      
  
  @property
  # compatibility -- remove when we remove support for deprecated name "action"
  def action(self):
    return self.leaf
  
  
  _canonical_leaf = None
  @property
  def canonical_leaf(self):
    if self._canonical_leaf is None:
      self._canonical_leaf = _find_canonical_leaf(self.leaf, self.leaf)
      log.debug('%r.canonical_leaf = %r', self, self._canonical_leaf)
    return self._canonical_leaf
  
  
  @property
  def path(self):
    '''Canonical exposed path.
    
    :rtype: list
    '''
    return control.path_to(self.canonical_leaf)
  
  @property
  def uri(self):
    '''Canonical exposed URI.
    
    :rtype: string
    '''
    return control.uri_for(self.canonical_leaf)
  
  @property
  def template_path(self):
    '''Template path.
    
    :rtype: list
    '''
    return control.template_for(self.canonical_leaf)
  
  def __str__(self):
    if self.path:
      return '/'+'/'.join(self.path)
    else:
      return self.__repr__()
  
  def __repr__(self):
    return '%s(canonical_leaf=%r, uri=%r)' \
      % (self.__class__.__name__, self.canonical_leaf, self.uri)
  

class Filter(object):
  def match(self, method, url):
    '''Test this filter against *method* and *url*.
    
    :returns: (list args, dict params) or None if no match
    :rtype: tuple
    '''
    return None2
  

class RegExpFilter(Filter):
  def __init__(self, pattern, destination_path, regexp_flags=re.I, match_on_full_url=False, 
               methods=None, params={}):
    '''Create a new regular expressions-based filter.
    
    :param pattern:           Pattern
    :type  pattern:           string or re.Regex
    
    :param destination_path:  Path to leaf, expressed in internal canonical form.
                              i.e. "/controller/leaf".
    :type  destination_path:  string
    
    :param regexp_flags:      Defaults to ``re.I`` (case-insensitive)
    :type  regexp_flags:      int
    
    :param match_on_full_url: Where there or not to perform matches on complete
                              URL (i.e. "https://foo.tld/bar?question=2").
                              Defauts to False (i.e.matches on path only. "/bar")
    :type  match_on_full_url: bool
    
    :param params:            Parameters are saved and later included in every call to
                              leafs taking this route.
    :type  params:            dict
    '''
    if not isinstance(regexp_flags, int):
      regexp_flags = 0
    
    if isinstance(pattern, RegexType):
      self.pattern = pattern
    elif not isinstance(pattern, basestring):
      raise ValueError('first argument "pattern" must be a Regex object or a string, not %s'\
        % type(pattern).__name__)
    else:
      self.pattern = re.compile(pattern, regexp_flags)
    
    if not isinstance(destination_path, (basestring, URL)):
      raise ValueError('second argument "destination_path" must be a string or URL, not %s'\
        % type(destination_path).__name__)
    
    self.destination_path = _prep_path(destination_path)
    self.match_on_full_url = match_on_full_url
    self.params = params
    
    if isinstance(methods, (list, tuple)):
      self.methods = methods
    elif methods is not None:
      if not isinstance(methods, basestring):
        raise TypeError('methods must be a tuple or list of strings, '\
          'alternatively a string, not a %s.' % type(methods))
      self.methods = (methods,)
    else:
      self.methods = None
  
  def match(self, method, url):
    '''Test this filter against *method* and *url*.
    
    :returns: (list args, dict params) or None if no match
    :rtype: tuple
    '''
    if method  and  self.methods is not None  and  method not in self.methods\
    and  (not control.enable_reflection  or  method != 'OPTIONS'):
      return None2
    
    if self.match_on_full_url:
      m = self.pattern.match(unicode(url))
    else:
      m = self.pattern.match(unicode(url.path))
    
    if m is not None:
      if self.params:
        params = self.params.copy()
      else:
        params = {}
      for k,v in m.groupdict().items():
        params[k.encode('utf-8')] = v
      return [], params
    
    return None2
  
  def __repr__(self):
    return '<%s.%s(%r, %r, %r) @0x%x>' %\
      (self.__module__, self.__class__.__name__, \
      self.methods, self.pattern.pattern, self.destination_path, id(self))
  


class Router(object):
  '''
  Default router handling both RegExp mappings and class tree mappings.
  
  Consider the following tree of controllers::
  
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
  
  
  Now, this list shows what URIs would map to what begin called::
  
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
  
  def configure(self, config_key='smisk.mvc.routes'):
    filters = config.get(config_key, [])
    if not isinstance(filters, (list, tuple)):
      raise TypeError('configuration parameter %r must be a list' % config_key)
    for filter in filters:
      try:
        # Convert a list or tuple mapping
        if isinstance(filter, (tuple, list)):
          if len(filter) > 2:
            filter = {'methods':filter[0], 'pattern': filter[1], 'destination': filter[2]}
          else:
            filter = {'pattern': filter[0], 'destination': filter[1]}
        # Create a filter from the mapping
        dest = URL(filter['destination'])
        self.filter(filter['pattern'], dest, match_on_full_url=dest.scheme,
                    methods=filter.get('methods', None))
      except TypeError, e:
        e.args = ('configuration parameter %r must contain dictionaries or lists' % config_key,)
        raise
      except IndexError, e:
        e.args = ('%r in configuration parameter %r' % (e.message, config_key),)
        raise
      except KeyError, e:
        e.args = ('%r in configuration parameter %r' % (e.message, config_key),)
        raise
  
  def filter(self, pattern, destination_path, regexp_flags=re.I, match_on_full_url=False, 
             params={}, methods=None):
    '''Explicitly map an leaf to paths or urls matching regular expression `pattern`.
    
    :param pattern:           Pattern
    :type  pattern:           string or re.Regex
    
    :param destination_path:  Path to leaf, expressed in internal canonical form.
                              i.e. "/controller/leaf".
    :type  destination_path:  string
    
    :param regexp_flags:      Defaults to ``re.I`` (case-insensitive)
    :type  regexp_flags:      int
    
    :param match_on_full_url: Where there or not to perform matches on complete
                              URL (i.e. "https://foo.tld/bar?question=2").
                              Defauts to False (i.e.matches on path only. "/bar")
    :type  match_on_full_url: bool
    
    :param params:            Parameters are saved and later included in every call to
                              leafs taking this route.
    :type  params:            dict
    
    :rtype: RegExpFilter
    '''
    filter = RegExpFilter(pattern, destination_path, regexp_flags, match_on_full_url, methods)
    # already exists?
    for i in range(len(self.filters)):
      f = self.filters[i]
      if isinstance(f, RegExpFilter) and f.pattern.pattern == pattern and f.methods == methods:
        # replace
        self.filters[i] = filter
        log.debug('updated filter %r', filter)
        return filter
    self.filters.append(filter)
    log.debug('added filter %r', filter)
    return filter
  
  
  def __call__(self, method, url, args, params):
    '''
    Find destination for route `url`.
    
    :param method: HTTP method
    :type  method: str
    :param url: The URL to consider
    :type  url: smisk.core.URL
    :return: ('Destionation' ``dest``, list ``args``, dict ``params``).
             ``dest`` might be none if no route to destination.
    :rtype: tuple
    '''
    # Explicit mapping? (never cached)
    for filter in self.filters:
      dargs, dparams = filter.match(method, url)
      if dargs is not None:
        dargs.extend(args)
        dparams.update(params)
        return self._resolve_cached(filter.destination_path), dargs, dparams
    
    return self._resolve_cached(_prep_path(url.path)), args, params
  
  def _resolve_cached(self, raw_path):
    try:
      return self.cache[raw_path]
    except KeyError:
      dest = introspect.ensure_va_kwa(self._resolve(raw_path))
      if dest is not None:
        dest = Destination(dest)
      self.cache[raw_path] = dest
      return dest
  
  def _resolve(self, raw_path):
    # Tokenize path
    path = tokenize_path(raw_path)
    node = control.root_controller()
    cls = node
    
    log.debug('resolving %s (%r) on tree %r', raw_path, path, node)
    
    # Check root
    if node is None:
      return wrap_exc_in_callable(http.ControllerNotFound('No root controller exists'))
    
    # Special case: empty path == root.__call__
    if not path:
      try:
        node = node().__call__
        log.debug('found leaf: %s', node)
        return node
      except AttributeError:
        return wrap_exc_in_callable(http.MethodNotFound('/'))
    
    # Traverse tree
    for part in path:
      log.debug('looking at part %r', part)
      found = None
      
      # 1. Search subclasses first
      log.debug('matching %r to subclasses of %r', part, node)
      try:
        subclasses = node.__subclasses__()
      except AttributeError:
        log.debug('node %r does not have subclasses -- returning MethodNotFound')
        return wrap_exc_in_callable(http.MethodNotFound(raw_path))
      for subclass in node.__subclasses__():
        if _node_name(subclass, subclass.controller_name()) == part:
          if getattr(subclass, 'hidden', False):
            continue
          found = subclass
          break
      if found is not None:
        node = found
        cls = node
        continue
      
      # 2. Search methods
      log.debug('matching %r to methods of %r', part, node)
      # Aquire instance
      if type(node) is type:
        node = node()
      for k,v in node.__dict__.items():
        if _node_name(v, k.lower()) == part:
          # If the leaf is hidden, we skip it
          if getattr(v, 'hidden', False):
            continue
          # If the leaf is not defined directly on parent node node, and
          # node.delegate evaluates to False, we bail out
          if not control.leaf_is_visible(v, cls):
            node = None
          else:
            found = v
          break
      
      # Check found node
      if found is not None:
        node = found
        node_type = type(node)
        # The following two lines enables accepting prefix routes:
        #if node_type is MethodType or node_type is FunctionType:
        #  break
      else:
        # Not found
        return wrap_exc_in_callable(http.MethodNotFound(raw_path))
    
    # Did we hit a class/type at the end? If so, get its instance.
    if type(node) is type:
      try:
        cls = node
        node = cls().__call__
        if not control.leaf_is_visible(node, cls):
          node = None
      except AttributeError:
        # Uncallable leaf
        node = None
    
    # Not callable?
    if node is None or not callable(node):
      return wrap_exc_in_callable(http.MethodNotFound(raw_path))
    
    log.debug('found leaf: %s', node)
    return node
  
