#!/usr/bin/env python
# encoding: utf-8
"""
Path to structure routing.
"""

import logging, re
from types import *
from exceptions import *
from smisk.core import URL
from control import Controller
import http

log = logging.getLogger(__name__)


def a(*args, **kwargs):
  raise http.MovedPermanently('/'+is__call__)

def wrap_exc_in_action(exc):
  def a(*args, **kwargs):
    raise exc
  return a

# xxx todo: when appropriate, control action and make sure it accepts at least (*args, **params)

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
  
  def __init__(self, action, path):
    self.action = action
    self.path = path
  
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
  def __init__(self, regexp, action, path, match_on_full_url=False):
    super(RegExpDestination, self).__init__(action, path)
    self.pattern = regexp
    self.match_on_full_url = match_on_full_url
  
  def match(self, url):
    if not self.match_on_full_url:
      url = url.path
    else:
      url = str(url)
    m = self.pattern.match(url)
    if m is not None:
      return self, m.groups(), m.groupdict()
  


class Router(object):
  """Abstract router"""
  None3Tuple = (None, None, None)
  
  def __init__(self, app=None):
    self.app = app
    self.mappings = []
  
  def __call__(self, url, root=None):
    raise NotImplementedError('abstract class Router is not callable')
  
  @property
  def root_controller(self):
    if not hasattr(self, '_root_controller'):
      self._root_controller = None
      for c in Controller.__subclasses__():
        if c.__name__.lower() == 'root':
          self._root_controller = c
    return self._root_controller
  
  
  def map(self, regexp, action, match_on_full_url=False):
    '''Explicitly map an action to urls matching regexp'''
    path = ['__call__'] # xxx todo: find a way to map the internal canonical path in this case.
    self.mappings.append(RegExpDestination(re.compile(regexp), action, path, match_on_full_url))
  
  
  def match_mapping(self, url):
    for dest in self.mappings:
      dest_args_params_tuple = dest.match(url)
      if dest_args_params_tuple is not None:
        return dest_args_params_tuple
    return self.None3Tuple
  

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
  
  
  def path_for_action(self, action):
    '''
    Can be called on an action which has been resolved at least once,
    to build and return its canonical internal path.
    
    :param action: The action
    :type  action: callable
    :rtype:        list
    '''
    root = self.root_controller
    
    if isinstance(action, root):
      path = ['__call__']
      if action.__class__ is root:
        return path
      n = action.__class__
    else:
      path = [action.__name__]
      if type(action) is MethodType:
        n = action.im_class
      else:
        n = action.parent
    
    while n is not root:
      path.append(n.__name__)
      if type(n) is MethodType:
        n = n.im_class
      else:
        n = n.parent
    path.reverse()
    return path
  
  
  def __call__(self, url, args, params):
    # First, see if an explicit mapping matches
    destination, dargs, dparams = self.match_mapping(url)
    if destination is not None:
      if dargs:
        args.extend(dargs)
      if dparams:
        dparams.update(dparams)
        params = dparams
      return destination
    
    # Now, go on matching on the controller tree as usual
    raw_path = url.path.strip('/')
    
    # Cached?
    if raw_path in self.cache:
      destination = self.cache[raw_path]
      if log.level <= logging.DEBUG:
        log.debug('Found destination in cache: %s', destination)
      return destination
    
    if log.level <= logging.DEBUG:
      log.info('Resolving %s', repr(raw_path))
    
    # Make sure we have a valid root
    root = self.root_controller
    if root is None:
      # XXX todo
      e = http.ControllerNotFound('No root controller could be found')
      self.cache[raw_path] = e
      raise e
    
    # a/b//c => ['a', 'b', 'c']
    path = []
    for part in raw_path.split('/'):
      part = URL.decode(part)
      if len(part):
        p = part.rfind('.')
        if p != -1:
          part = part[:p]
          if len(part):
            path.append(part)
        else:
          path.append(part)
    
    is__call__ = len(path) > 0 and path[-1] == '__call__'
    if is__call__:
      is__call__ = '/'.join(path[:-1])
    
    # Find branch
    action = root
    action.parent = None
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
        found_sub_cls.parent = action
        action = found_sub_cls
        last_match_index = i
      else:
        # Aquire controller instance, as all controllers are singletons, this is safe
        if action is not MethodType:
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
                if __debug__:
                  log.debug('Found member %s %s for part %s on %s', 
                            member_name, repr(member), part, repr(action))
                if member_type is not MethodType:
                  member.__class__.parent = action.__class__
                action = member
                if i == len(path)-1:
                  end_of_branch = True
                last_match_index = i
                break
              elif __debug__:
                log.debug('Skipping member %s %s for part %s on %s', 
                          member_name, repr(member), part, repr(action))
            
        # Revert to class if we are to continue
        if not end_of_branch:
          #log.debug('R not end_of_branch')
          action = action.__class__
      
      # If we did hit a method, or a leaf, this is the end of the branch  
      if end_of_branch:
        break
    
    # Did we just end up on a class branch?
    if not end_of_branch:
      if last_match_index+1 != len(path):
        action = None
      else:
        # Set action to the instance of the class rather than the class itself
        if type(action) is TypeType:
          action = action()
      # Make sure the action (class instance) is callable
      if not callable(action):
        a = wrap_exc_in_action(http.MethodNotFound('No such method: "%s"' % '.'.join(path)))
        self.cache[raw_path] = a
        a()
    
    # Calc path
    path = self.path_for_action(action)
    
    # Redirect /something/__call__ to /something
    if is__call__ is not False:
      def a(*args, **kwargs):
        raise http.MovedPermanently('/'+is__call__)
      action = a
    
    # Make destination
    destination = Destination(action, path)
    if log.level <= logging.DEBUG:
      log.debug('Found destination: %s', repr(destination))
    
    # Cache the results
    self.cache[raw_path] = destination
    
    return destination
  
