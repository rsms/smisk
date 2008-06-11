#!/usr/bin/env python
# encoding: utf-8
"""
Path to structure routing.
"""

import logging
from types import *
from exceptions import *
from ..core import URL
from control import Controller

log = logging.getLogger(__name__)


class Destination(object):
  # These should not be modified directly from outside of a router,
  # since routers might cache instances of Destination.
  action = None
  
  def __call__(self, *args, **kwargs):
    return self.action(*args, **kwargs)
  


class Router(object):
  """Abstract router"""
  def __init__(self, app=None):
    self.app = app
  
  def __call__(self, url, root=None):
    raise NotImplementedError('Abstract class Router is not callable')
  
  @property
  def root_controller(self):
    if not hasattr(self, '_root_controller'):
      self._root_controller = None
      for c in Controller.__subclasses__():
        if c.__name__.lower() == 'root':
          self._root_controller = c
    return self._root_controller
  

class ClassTreeRouter(Router):
  """
  Maps a path to a callable in a class tree.
  
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
  
  Of course, there is only one persistent instance of any controller.
  
  """
  
  def __init__(self, *args, **kwargs):
    super(ClassTreeRouter, self).__init__(*args, **kwargs)
    self.cache = {}
  
  def __call__(self, url, root=None):
    raw_path = url.path.strip('/')
    
    # Cached?
    if raw_path in self.cache:
      destination = self.cache[raw_path]
      log.debug('Found destination in cache: %s', destination)
      return destination
    
    log.info('Resolving %s', repr(raw_path))
    destination = Destination()
    
    # Make sure we have a valid root
    if root is None:
      root = self.root_controller
    if root is None:
      raise ControllerNotFound('No root controller could be found')
    
    # a/b//c => ['a', 'b', 'c']
    path = []
    for part in raw_path.split('/'):
      part = URL.decode(part)
      if len(part):
        path.append(part)
    
    # Find branch
    action = root
    end_of_branch = False
    last_match_index = -1
    for i in range(len(path)):
      part = path[i]
      # 1. Find subclass  named <string part> of <class action>
      found_sub_cls = None
      #log.debug('R looking for part %s in %s.__subclasses__', part, repr(action))
      for cls in action.__subclasses__():
        if cls.__name__.lower() == part:
          #log.debug('R found subclass %s for part %s on %s', repr(cls), part, repr(action))
          found_sub_cls = cls
          break
      
      if found_sub_cls is not None:
        action = found_sub_cls
        last_match_index = i
      else:
        # Aquire controller instance, as all controllers are singletons, this is safe
        action = action()
        # 2. find method  named <string part> of <class action>
        # Note: we do search subclasses but we do NOT search for anything within methods or other
        #       members which are not a class. Otherwise we would get problems.
        for member_name in dir(action):
          if member_name.lower() == part:
            member = getattr(action, member_name)
            if callable(member):
              member_type = type(member)
              # Make sure it's a callable member
              if member_type is TypeType or member_type is ClassType:
                member = member()
                if not callable(member):
                  member = None
              elif member_type is not MethodType:
                # uncallable member
                member = None
              
              if member is not None:
                log.debug('Found member %s %s for part %s on %s', member_name, repr(member), part, repr(action))
                action = member
                end_of_branch = True
                last_match_index = i
                break
              else:
                log.debug('Skipping member %s %s for part %s on %s', member_name, repr(member), part, repr(action))
            
        # Revert to class if we are to continue
        if not end_of_branch:
          action = action.__class__
      
      # If we did hit a method, or a leaf, this is the end of the branch  
      if end_of_branch:
        break
    
    # Did we just end up on a class branch?
    if not end_of_branch:
      if last_match_index+1 != len(path):
        raise MethodNotFound('No such method: "%s"' % '.'.join(path))
      # Set action to the instance of the class rather than the class itself
      if type(action) is TypeType:
        action = action()
      # Make sure the action (class instance) is callable
      if not callable(action):
        raise MethodNotFound('No such method: "%s"' % '.'.join(path))
    
    # Complete destination
    destination.action = action
    log.debug('Found destination: %s', repr(destination))
    
    # Cache the results
    self.cache[raw_path] = destination
    
    return destination
  
