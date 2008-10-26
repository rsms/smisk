# encoding: utf-8
'''Control in MVC – Base Controller and helpers like function-to-URL conversion.
'''
import re, logging
from types import *
from smisk.inflection import inflection
from smisk.util.string import tokenize_path
from smisk.util.python import classmethods
from smisk.util.introspect import introspect
from smisk.util.type import Undefined
from smisk.util.cache import callable_cache_key
from smisk.mvc.decorators import expose

_root_controller = False
_path_to_cache = {}
_template_for_cache = {}
_uri_for_cache = {}

log = logging.getLogger(__name__)

def root_controller():
  '''Returns the root controller.
  
  :rtype: Controller'''
  global _root_controller
  if _root_controller is not False:
    return _root_controller
  for c in Controller.__subclasses__():
    if c.__name__.lower() == 'root':
      _root_controller = c
      return _root_controller


def controllers():
  '''Available controllers as a list, incuding the root.
  
  :returns: List of controller instances in an undefined order.
  :rtype: list
  '''
  root = root_controller()
  _controllers = [root()]
  def _r(baseclass, v):
    for subclass in baseclass.__subclasses__():
      v.append(subclass())
      _r(subclass, v)
  _r(root, _controllers)
  return _controllers


def node_name(node):
  '''Name of an exposed node.
  
  :param node:
  :type  node: callable
  :returns: The name of `node` or ``None`` if node is not exposed. Note that
            this function returns the empty string ("") if `node` is the root
            controller.
  :rtype: string
  '''
  path = path_to(node)
  if path is not None:
    try:
      return path_to(node)[-1]
    except IndexError:
      return ''


def uri_for(node):
  '''Returns the canonical exposed URI of a node.
  
  If node is a controller or a __call__, the uri always ends in a slash.
  Otherwise it never ends in a slash. 
  
  :param node:
  :type  node: callable
  :rtype: string
  '''
  cache_key = callable_cache_key(node)
  try:
    return _uri_for_cache[cache_key]
  except KeyError:
    path = path_to(node)
    if path is None:
      uri = None
    else:
      uri = '/'+'/'.join(path)
      if len(path) > 0 and \
        (not isinstance(node, (MethodType, FunctionType)) or node.__name__ == '__call__'):
        uri += '/'
    _uri_for_cache[cache_key] = uri
    return uri


def path_to(node):
  '''Returns the canonical path to node.
  
  :param node: Something on the controller tree. (method, class, instance, etc)
  :type  node: object
  :rtype: list'''
  global _path_to_cache
  return _cached_path_to(callable_cache_key(node), node, _path_to_cache, False)


def template_for(node):
  '''Returns the template uri for node.
  
  :param node: Something on the controller tree. (method, class, instance, etc)
  :type  node: object
  :rtype: list'''
  global _template_for_cache
  return _cached_path_to(callable_cache_key(node), node, _template_for_cache, True)


def method_origin(method):
  '''Return the class on which `method` was originally defined.
  
  .. python::
    >>> class Animal(object):
    >>>   def name(self):
    >>>     pass
    >>> 
    >>> class Fish(Animal):
    >>>   def color(self):
    >>>     pass
    >>> 
    >>> o = Fish()
    >>> 
    >>> print method_origin(o.name)
    <class '__main__.Animal'>
    >>> print method_origin(o.color)
    <class '__main__.Fish'>
  
  :param    method:
  :type     method: callable
  :returns: Class on which `method` was originally defined
  :rtype:   object
  '''
  try:
    return _method_origin_r(method.im_func, method.im_class)
  except AttributeError:
    raise ValueError('first argument "method" is missing attributes "im_class" and "im_func"')


def _method_origin_r(func, baseclass):
  for subclass in baseclass.__bases__:
    member = getattr(subclass, func.__name__, None)
    if member is not None and isinstance(member, MethodType) \
        and member.im_func.func_code == func.func_code:
      return _method_origin_r(func, subclass)
  return baseclass


def leaf_is_visible(node, cls=None):
  '''Return True if `node` defined on class `cls` is visible.
  
  :param  cls:
  :type   cls: class
  :param  node:
  :type   node: object
  :rtype: bool
  '''
  if not isinstance(node, (MethodType, FunctionType)):
    try:
      node = node.__call__
    except AttributeError:
      return False
  if getattr(node, 'hidden', False):
    return False
  try:
    delegates = node.delegates
  except AttributeError:
    delegates = False
  if cls is None:
    try: cls = node.im_class
    except AttributeError: pass
  if cls is None:
    if not delegates:
      return False
  elif not delegates:
    origin = method_origin(node)
    if origin is Controller \
        and Controller.smisk_enable_specials \
        and cls is root_controller() \
        and node.__name__.startswith('smisk_'):
      # the special methods on the root controller
      return True
    elif origin != cls:
      return False
  return True


def _cached_path_to(cache_key, node, cache, resolve_template):
  try:
    return cache[cache_key]
  except TypeError:
    return None
  except KeyError:
    path = _path_to(node, resolve_template)
    if path:
      if not resolve_template and path[0] == '__call__':
        path = path[1:]
      path.reverse()
    cache[cache_key] = path
    return path


def _node_name(node, fallback):
  '''Name of node
  
  :rtype: unicode
  '''
  try:
    slug = node.slug
    if slug is not None:
      return unicode(slug)
  except AttributeError:
    pass
  return fallback


def _get_template(node):
  tpl = getattr(node, 'template', None)
  if tpl is not None:
    if not isinstance(tpl, list):
      tpl = tokenize_path(str(tpl))
    return tpl


def _path_to(node, resolve_template):
  if isinstance(node, (MethodType, FunctionType)):
    # Leaf is Method or Function.
    # Function supported because methods might be wrapped in functions
    # which in those cases should have an im_class attribute.
    if getattr(node, 'im_class', None) is None \
        or getattr(node, 'im_func', None) is None \
        or not issubclass(node.im_class, root_controller()):
      return None
    
    if not leaf_is_visible(node):
      return None
    
    if resolve_template:
      tpl = _get_template(node)
      if tpl is not None:
        return tpl
    
    path = [_node_name(node, node.im_func.__name__)]
    path = _path_to_class(node.im_class, path)
  else:
    # Leaf is Class
    if not isinstance(node, TypeType):
      node = node.__class__
    
    assert isinstance(node, TypeType)
    
    try:
      node_callable = node.__call__
    except AttributeError:
      return None
    
    if not leaf_is_visible(node_callable, node):
      return None
    
    if resolve_template:
      tpl = _get_template(node)
      if tpl is not None:
        return tpl
    
    name = _node_name(node_callable, None)
    if name is None and resolve_template:
      path = [u'__call__']
    else:
      path = []
    
    path = _path_to_class(node, path)
  
  if path is not None and None in path:
    return None
  
  return path


def _path_to_class(node, path):
  root = root_controller()
  if getattr(node, 'hidden', False) or not issubclass(node, root):
    return None
  if node is root:
    return path
  path.append(_node_name(node, node.controller_name()))
  try:
    return _path_to_class(node.__bases__[0], path)
  except IndexError:
    return path


def _filter_dict(d, rex):
  if rex is not None:
    rex = unicode(rex).strip()
    if rex:
      dd = {}
      try:
        rex = re.compile('.*%s.*' % rex, re.I)
        for k in d:
          if rex.match(k):
            dd[k] = d[k]
        return dd
      except re.error:
        pass
  return d


def _doc_intro(entity):
  s = []
  if not entity.__doc__:
    return u''
  for ln in unicode(entity.__doc__).strip().split('\n'):
    ln = ln.strip()
    if not ln:
      break
    s.append(ln)
  return u'\n'.join(s)


class Controller(object):
  '''The base controller from which the controller tree is grown.
  
  To grow a controller tree, you need to set a root first. This is done by defining a subclass of `Controller` with the special name 'root' (case-insensitive).
  
  Here is a very simple, but valid, controller tree:
  
  .. python::
    class root(Controller):
      def hello(self):
        return {'message': 'Hello'}
  
  '''
  
  smisk_enable_specials = True
  '''Enable exposure of the special ``smisk:``-methods.
  
  These special methods are defined in ``Controller`` prefixed ``smisk_``,
  but actually exposed on the *root controller*.
  
  It is recommended to have this set to ``True``, as some clients might 
  rely on the *reflection* provided by these special methods.
  
  :type: bool
  :see: `special_methods()`
  '''
  
  def __new__(typ):
    if not '_instance' in typ.__dict__:
      o = object.__new__(typ)
      class_meths = classmethods(typ)
      for k in dir(o):
        v = getattr(o, k)
        if (k[0] != '_' or getattr(v, 'slug', False)) and k not in class_meths:
          o.__dict__[k] = v
      typ._instance = o
    return typ._instance
  
  @classmethod
  def controller_name(cls):
    '''Returns the canonical name of this controller.
    
    :rtype: string'''
    try:
      return cls.slug
    except AttributeError:
      return inflection.underscore(cls.__name__.replace('Controller',''))
  
  @classmethod
  def controller_path(cls):
    '''Returns the canonical path to this controller.
    
    :returns: path as token list or None if no path to this controller.
    :rtype: list'''
    return path_to(cls)
  
  @classmethod
  def controller_uri(cls):
    '''Returns the canonical URI for this controller.
    
    :rtype: string'''
    return uri_for(cls)
  
  @classmethod
  def special_methods(cls):
    '''Returns a dictionary of available special methods, keyed by exposed name.
    
    :see: `smisk_enable_specials`
    :rtype: list
    '''
    specials = {}
    for k in dir(Controller):
      if k.startswith('smisk_'):
        v = getattr(Controller, k)
        if isinstance(v, (MethodType, FunctionType)):
          node_name = k
          try:
            slug = v.slug
            if slug is not None:
              node_name = unicode(slug)
          except AttributeError:
            pass
          specials[node_name] = v
    return specials
  
  @expose('smisk:methods')
  def smisk_methods(self, filter=None, *args, **params):
    '''List available methods.
    
    :param filter: Only list methods which URI matches this regular expression.
    :type filter:  string
    :returns: Methods keyed by URI
    '''
    try:
      methods = self._methods_cached
    except AttributeError:
      methods = {}
      for controller in controllers():
        leafs = controller.__dict__.values()
        leafs.append(controller)
        for leaf in leafs:
          if not isinstance(leaf, (MethodType, FunctionType, ClassType, TypeType)):
            continue
          if path_to(leaf) is None:
            continue
          info = introspect.callable_info(leaf)
          
          params = {}
          for k,v in info['args']:
            if v is not Undefined:
              v = 'optional'
            else:
              v = 'required'
            params[k] = v
          
          try:
            formats = leaf.formats
          except AttributeError:
            formats = ['*']
          
          if leaf.__doc__:
            descr = _doc_intro(leaf)
          else:
            descr = ''
          
          m = {
            'params': params,
            'description': descr,
            'formats': ', '.join(formats)
          }
          methods[uri_for(leaf)] = m
      self._methods_cached = methods
    return _filter_dict(methods, filter)
  
  
  @expose('smisk:charsets')
  def smisk_charsets(self, filter=None, *args, **params):
    '''List available character sets.
    
    :param filter: Only list charsets matching this regular expression.
    :type filter:  string
    :returns: Character sets keyed by name
    '''
    from smisk.charsets import charsets
    return _filter_dict(charsets, filter)
  
  
  @expose('smisk:codecs')
  def smisk_codecs(self, filter=None, *args, **params):
    '''List available content codecs.
    
    :param filter: Only list codecs which name matches this regular expression.
    :type filter:  string
    :returns: Codecs keyed by name
    '''
    import smisk.codec
    codecs = {}
    for codec in smisk.codec.codecs:
      codecs[codec.name] = {
        'extensions': ', '.join(codec.extensions),
        'media_types': ', '.join(codec.media_types),
        'description': _doc_intro(codec),
        'directions': ', '.join(codec.directions())
      }
    return _filter_dict(codecs, filter)
  
  
  def __repr__(self):
    uri = self.controller_uri()
    if uri is None:
      uri = '<None>'
    else:
      uri = '"%s"' % uri
    return '<Controller %s %s>' % (self.__class__.__name__, uri)
  
