# encoding: utf-8
from types import MethodType
from smisk.inflection import inflection
from smisk.util import tokenize_path

_root_controller = False
_path_to_cache = {}
_template_for_cache = {}

def root_controller():
  '''Returns the root controller.
  
  :rtype: Controller'''
  global _root_controller
  if _root_controller is False:
    _root_controller = None
    for c in Controller.__subclasses__():
      if c.__name__.lower() == 'root':
        _root_controller = c
  return _root_controller


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
    if path is not None:
      path.reverse()
    cache[node] = path
    return path


def _node_name(node, fallback):
  n = getattr(node, 'slug', None)
  if n is None:
    return fallback
  return n

def _get_template(node):
  tpl = getattr(node, 'template', None)
  if tpl is not None:
    if not isinstance(tpl, list):
      tpl = tokenize_path(str(tpl))
    return tpl

def _path_to(node, resolve_template):
  node_type = type(node)
  
  if node_type is MethodType:
    # Leaf is Method
    if getattr(node, 'hidden', False):
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
    except KeyError:
      return None
    
    if getattr(node_callable, 'hidden', False):
      return None
    
    if resolve_template:
      tpl = _get_template(node)
      if tpl is not None:
        return tpl
    
    name = _node_name(node_callable, None)
    if name is None:
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


class Controller(object):
  def __new__(typ):
    if not '_instance' in typ.__dict__:
      o = object.__new__(typ)
      for k in dir(o):
        if k[0] != '_':
          o.__dict__[k] = getattr(o, k)
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
    return path_to(cls)[:-1]
  
  def __repr__(self):
    return '<Controller %s@%s>' % (self.__class__.__name__, '.'.join(['root'] + self.controller_path()))
  
