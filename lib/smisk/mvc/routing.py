#!/usr/bin/env python
# encoding: utf-8
"""
Path to structure routing.
"""

import logging
from types import *
from smisk.core import URL
from smisk.mvc.control import Controller

log = logging.getLogger(__name__)


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
  
  >>> class root(Controller):
  >>>   def __call__(self, *args, **params):
  >>>     return 'Welcome!'
  >>>
  >>> class employees(root):
  >>>   def __call__(self, *args, **params):
  >>>     return {'employees': Employee.query.all()}
  >>>
  >>>   def show(self, employee_id, *args, **params):
  >>>     return {'employee': Employee.get_by(id=employee_id)}
  >>>
  >>>   class edit(employees):
  >>>     def __call__(self, employee_id, *args, **params):
  >>>       return employees.show(self, employee_id)
  >>>
  >>>     def save(self, employee_id, *args, **params):
  >>>       Employee.get_by(id=employee_id).save_or_update(**params)
  >>>
  
  Now, this list shows what URIs would map to what begin called:
  
  /                             => root().__call__()
  /employees                    => employees().__call__()
  /employees/                   => employees().__call__()
  /employees/show               => employees().show()
  /employees/show/123           => employees().show(123)
  /employees/show/123/456       => employees().show(123, 456)
  /employees/show/123?other=456 => employees().show(123, other=456)
  /employees/edit/123           => employees.edit().__call__(123)
  
  Of course, there is only one persistent instance of any controller.
  
  """
  
  def __init__(self, *args, **kwargs):
    super(ClassTreeRouter, self).__init__(*args, **kwargs)
    self.cache = {}
  
  def __call__(self, url, root=None):
    raw_path = url.path.strip('/')
    
    # Cached?
    if raw_path in self.cache:
      action = self.cache[raw_path]
      log.debug('Found action in cache: %s', repr(action))
      return action
    
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
    for part in path:
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
      else:
        # Aquire controller instance, as all controllers are Singletons, this is safe
        action = action()
        # 2. find method  named <string part> of <class action>
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
                log.debug('found member %s %s for part %s on %s', member_name, repr(member), part, repr(action))
                action = member
                end_of_branch = True
                break
              else:
                log.debug('skipping member %s %s for part %s on %s', member_name, repr(member), part, repr(action))
            
        # Revert to class if we are to continue
        if not end_of_branch:
          action = action.__class__
      
      # If we did hit a method, or a leaf, this is the end of the branch  
      if end_of_branch:
        break
    
    # Did we just end up on a class branch?
    if not end_of_branch:
      # Set action to the instance of the class rather than the class itself
      if isinstance(action, type):
        action = action()
      # Make sure the action (class instance) is callable
      if not callable(action):
        raise ActionNotFound('%s is not callable' % repr(action))
    
    log.debug('Found action: %s', repr(action))
    
    # Cache the results
    self.cache[raw_path] = action
    
    return action
  
