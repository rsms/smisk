# encoding: utf-8
'''Control in MVC – Base Controller and helpers like function-to-URL conversion.
'''
import re, logging
from types import *
from smisk.inflection import inflection
from smisk.util import tokenize_path, classmethods, introspect, Undefined
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
  
  :rtype: list
  '''
  node = root_controller()
  _controllers = [node()]
  def _r(node):
    for c in node.__subclasses__():
      _controllers.append(c())
      _r(c)
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
  '''Returns the canonical exposed URI of a node.'''
  try:
    return _uri_for_cache[node]
  except KeyError:
    path = path_to(node)
    if path is None:
      uri = None
    else:
      uri = '/'+'/'.join(path)
      if len(path) > 1 and (isinstance(node, Controller) or node.__name__ == '__call__'):
        uri += '/'
    _uri_for_cache[node] = uri
    return uri


def path_to(node):
  '''Returns the canonical path to node.
  
  :param node: Something on the controller tree. (method, class, instance, etc)
  :type  node: object
  :rtype: list'''
  global _path_to_cache
  return _cached_path_to(node, _path_to_cache, False)


def template_for(node):
  '''Returns the template uri for node.
  
  :param node: Something on the controller tree. (method, class, instance, etc)
  :type  node: object
  :rtype: list'''
  global _template_for_cache
  return _cached_path_to(node, _template_for_cache, True)


def _cached_path_to(node, cache, resolve_template):
  try:
    return cache[node]
  except KeyError:
    path = _path_to(node, resolve_template)
    if path:
      if not resolve_template and path[0] == '__call__':
        path = path[1:]
      path.reverse()
    cache[node] = path
    return path


def _node_name(node, fallback):
  try:
    return node.slug
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
  node_type = type(node)
  
  if node_type in (MethodType, FunctionType):
    # Leaf is Method or Function
    if getattr(node, 'hidden', False) \
        or getattr(node, 'im_class', None) is None \
        or not issubclass(node.im_class, root_controller()):
      return None
    
    if resolve_template:
      tpl = _get_template(node)
      if tpl is not None:
        return tpl
    
    path = [_node_name(node, node.im_func.__name__)]
    path = _path_to_class(node.im_class, path)
    
  else:
    # Leaf is Class
    if node_type is not type:
      node = node.__class__
    
    try:
      node_callable = node.__call__
    except AttributeError:
      return None
    
    if getattr(node_callable, 'hidden', False):
      return None
    
    if resolve_template:
      tpl = _get_template(node)
      if tpl is not None:
        return tpl
    
    name = _node_name(node_callable, None)
    if name is None and resolve_template:
      path = ['__call__']
    else:
      path = []
    
    path = _path_to_class(node, path)
  
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
  def __new__(typ):
    try:
      return typ._instance
    except AttributeError:
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
    return inflection.underscore(cls.__name__.replace('Controller',''))
  
  @classmethod
  def controller_path(cls):
    '''Returns the canonical path to this controller.
    
    :rtype: list'''
    return path_to(cls)
  
  @classmethod
  def controller_uri(cls):
    '''Returns the canonical URI for this controller.
    
    :rtype: string'''
    return uri_for(cls)
  
  @expose('smisk:methods')
  def _methods(self, filter=None, *args, **params):
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
        leafs.append(controller.__call__)
        for leaf in leafs:
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
  def _charsets(self, filter=None, *args, **params):
    '''List available character sets.
    
    :param filter: Only list charsets matching this regular expression.
    :type filter:  string
    :returns: Character sets keyed by name
    '''
    from smisk.charsets import charsets
    return _filter_dict(charsets, filter)
  
  
  @expose('smisk:codecs')
  def _codecs(self, filter=None, *args, **params):
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
    return '<Controller %s@%s>' % (self.__class__.__name__, '.'.join(['root'] + self.controller_path()))
  
