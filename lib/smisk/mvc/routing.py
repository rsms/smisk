#!/usr/bin/env python
# encoding: utf-8
"""
A fast pathname-to-somethingpython mapper.

Created by Rasmus Andersson on 2007-05-15.
Copyright (c) 2007 Rasmus Andersson. All rights reserved.
"""
__revision__ = '$Revision: 0$'.split(' ')[1][:-1]
__docformat__ = 'restructuredtext en'

import re, logging
log = logging.getLogger(__name__)

class RouterException(Exception):
  """A problem with a `Router`"""

class DestinationNotFound(RouterException):
  """A problem with a `Destination`"""
  http_code = 404
    

class Destination(object):
  """A destination"""
  def __init__(self, pattern, **kwargs):
    self.pattern = pattern
    self.kwargs = kwargs
  
  def match(self, s):
    if s == self.pattern:
      return self.kwargs
  
  def __repr__(self):
    return "%s(pattern=%s, **kwargs=%s)" %\
      (self.__class__.__name__, repr(self.pattern), repr(self.kwargs))


class AnyDestination(Destination):
  """Matches anything"""
  def match(self, s):
    return self.kwargs
  

class PrefixDestination(Destination):
  """Matches string prefixes"""
  def __init__(self, pattern, **kwargs):
    Destination.__init__(self, pattern, **kwargs)
    self.pattern = self.pattern[:-1] # strip * from end
    self._patlen = len(self.pattern)
  
  def match(self, s):
    if s[:self._patlen] == self.pattern:
      return self.kwargs
  

class SuffixDestination(Destination):
  """Matches string suffixes"""
  def __init__(self, pattern, **kwargs):
    Destination.__init__(self, pattern, **kwargs)
    self.pattern = self.pattern[1:] # strip * from beginning
    self._patlen = -len(self.pattern)
  
  def match(self, s):
    if s[self._patlen:] == self.pattern:
      return self.kwargs
  

class RegExpDestination(Destination):
  """Match using Regular Expressions"""
  def match(self, s):
    """docstring for match"""
    m = self.pattern.match(s)
    if m:
      d = self.kwargs.copy()
      d.update(m.groupdict())
      return d
    return None
  
  def __repr__(self):
    return "%s(pattern=%s, **kwargs=%s)" %\
      (self.__class__.__name__, repr(self.pattern.pattern), repr(self.kwargs))
  

class KeywordDestination(RegExpDestination):
  """Matches strings with keywords.
  
  Example:
  ``'/foo/:bar/:action' -> '/foo/hello/john' = {'bar':'hello', 'action':'john'}``
  
  Expects ``s`` to always start with a ``/`` character.
  
  Keywords are parsed and passed on when ``__call__``ing a destination.
  """
  def __init__(self, pattern, **kwargs):
    Destination.__init__(self, pattern, **kwargs)
    pat = [r"^"]
    for w in self.pattern.strip('/').split('/'):
      if w[0] == ':':
        w = w[1:]
        pat.append("(?:/(?P<%s>[^/]+)|)" % w)
        if w not in kwargs:
          kwargs[w] = None
      else:
        pat.append("/"+w)
    pat.append(r"/?$")
    self.pattern = re.compile(''.join(pat))
    #self.pattern = re.compile(r"^/bar(?:/(?P<controller>\w+)|)(?:/(?P<action>\w+)|)/?$")
  

class Router(object):
  """Map url paths to objects."""
  def __init__(self):
    self.destinations = []
    self.anyDestination = None
  
  def map(self, pattern, **kwargs):
    """Map a url path pattern to something.
    
    **Note:** The new destination is put at first priority (beginning of array),
    not appended to the end.
    
    :rtype: Destination
    """
    if pattern is None:
      DestCLASS = AnyDestination
    else:
      DestCLASS = Destination
      try:
        x = pattern.pattern
        DestCLASS = RegExpDestination
      except AttributeError:
        if pattern.find(':') != -1:
          DestCLASS = KeywordDestination
        elif pattern[0] == '*':
          DestCLASS = SuffixDestination
        elif pattern[-1] == '*':
          DestCLASS = PrefixDestination
    
    destination = DestCLASS(pattern, **kwargs)
    log.debug('mapping %s', destination)
    if DestCLASS == AnyDestination:
      self.anyDestination = destination
    else:
      self.destinations.append(destination)
    return destination
  
  def __call__(self, path):
    """Route a path to a destination.
    
    :type   path:            string
    :rtype:                  Destination
    :raises RouterException: if no route was found"""
    log.debug('routing %s', path)
    for destination in self.destinations:
      log.debug('testing %s', destination)
      match = destination.match(path)
      if match:
        log.debug('match %s -> %s', destination, match)
        return match
    if self.anyDestination:
      log.debug('match %s', self.anyDestination)
      return self.anyDestination.match(path)
    raise DestinationNotFound("No destination for %s" % repr(path))
  


if __name__ == '__main__':
  from miwa.tests.routing import *
  unittest.main()