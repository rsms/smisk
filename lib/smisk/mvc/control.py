# encoding: utf-8
from types import MethodType
from smisk.inflection import inflection

_root_controller = False
_path_to_cache = {}

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
  try:
    return _path_to_cache[node]
  except KeyError:
    path = []
    node_type = type(node)
    if node_type is MethodType:
      path = [node.im_func.__name__]
      path = _path_to_class(node.im_class, path)
    else:
      path = ['__call__']
      if node_type is type:
        path = _path_to_class(node, path)
      else:
        path = _path_to_class(node.__class__, path)
    if path is not None:
      path.reverse()
    _path_to_cache[node] = path
    return path


def _path_to_class(node, path):
  root = root_controller()
  if node is root:
    return path
  if not issubclass(node, root):
    raise TypeError('%s is not part of the Controller tree' % node)
  path.append(node.controller_name())
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
  
