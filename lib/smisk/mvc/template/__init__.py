# encoding: utf-8
# Based on lookup.py from the Mako project
# Copyright (C) 2006, 2007, 2008 Michael Bayer mike_mp@zzzcomputing.com
#
# This module is part of Mako and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php
#
# Modified for Smisk by Rasmus Andersson.
#
'''View in MVC – Templating.

.. packagetree (xxx todo fix for Sphinx)

:requires: mako
'''
import os, sys, stat, posixpath, re, logging
import smisk.core.xml
from smisk.core import URL
from smisk import util
from smisk.mvc import http
import smisk.mvc
try:
  from mako import exceptions
  exceptions.TopLevelLookupException.status = http.NotFound
  from mako.util import LRUCache
  from mako.template import Template
  import mako.filters
  # Replace Mako filter with the faster Smisk C implementations
  mako.filters.html_escape = smisk.core.xml.escape
  mako.filters.xml_escape = smisk.core.xml.escape
  mako.filters.url_escape = URL.encode
  mako.filters.url_unescape = URL.decode
except ImportError:
  # mako is not installed
  Template = None

__all__ = ['Templates', 'Template']
log = logging.getLogger(__name__)


class Templates(object):
  cache_limit = -1
  '''Limit cache size.
  
  0 means no cache.
  -1 means no limit.
  any positive value results in a LRU-approach.
  
  :type: int
  '''
  
  cache_type = 'memory'
  '''Type of cache.
  
  :type: string
  '''
  
  imports = [
    'import os, sys, time, logging',
    'from smisk.core import app, request, response',
    'from smisk.mvc.template.filters import j',
    'log = logging.getLogger(\'template:\' + _template_uri)'
  ]
  ''':type: list'''
  
  autoreload = None
  '''Automatically reload templates which has been modified.
  
  If this is set to None when the application start accepting requests,
  the application will set the value according to its own autoreload value.
  
  :type: bool
  '''
  
  format_template_exceptions = True
  '''Let the templating engine render information about template formatting exceptions.
  
  Things like missing or misspelled variables etc.
  
  :type: bool
  '''
  
  directories = None
  '''Directories in which to find templates.
  
  :type: list
  '''
  
  errors = {}
  '''Map http error to a template path.
  
  i.e. 500: 'errors/server_error'
  
  :type: dict
  '''
  
  is_useable = Template is not None
  '''True if mako is installed and templating can be used'''
  
  def __init__(self):
    self.directories = []
    self.get_template = self.template_for_uri # for compat with mako
    self.reset_cache()
  
  def reset_cache(self):
    if self.cache_limit == -1:
      self.instances = {}
      self._uri_cache = {}
    else:
      self.instances = LRUCache(self.cache_limit)
      self._uri_cache = LRUCache(self.cache_limit)
  
  def template_for_uri(self, uri, exc_if_not_found=True):
    '''
    :return: template for the uri provided 
    :rtype:  Template
    '''
    try:
      template = self.instances[uri]
      if self.autoreload:
        if template is not None:
          template = self._check(uri, template)
        else:
          raise KeyError('check again')
      if exc_if_not_found and template is None:
        raise exceptions.TopLevelLookupException("Failed to locate template for uri '%s'" % uri)
      return template
    except KeyError:
      u = re.sub(r'^\/+', '', uri)
      for dn in self.directories:
        srcfile = posixpath.normpath(posixpath.join(dn, u))
        if os.access(srcfile, os.F_OK):
          return self._load(srcfile, uri)
      else:
        self.instances[uri] = None
        if exc_if_not_found:
          raise exceptions.TopLevelLookupException("Failed to locate template for uri '%s'" % uri)
        return None
  
  def adjust_uri(self, uri, relativeto):
    '''adjust the given uri based on the calling filename.'''
    if uri[0] != '/':
      if relativeto is not None:
        return posixpath.join(posixpath.dirname(relativeto), uri)
      else:
        return '/' + uri
    else:
      return uri
  
  def filename_to_uri(self, filename):
    try:
      return self._uri_cache[filename]
    except KeyError:
      value = self._relativeize(filename)
      self._uri_cache[filename] = value
      return value
  
  def render_error(self, status, params={}, format='html'):
    # Compile body from template
    if status.code in self.errors:
      template = self.template_for_uri('%s.%s' % (self.errors[status.code], format), False)
    elif status in self.errors:
      template = self.template_for_uri('%s.%s' % (self.errors[status], format), False)
    elif 0 in self.errors:
      template = self.template_for_uri('%s.%s' % (self.errors[0], format), False)
    else:
      template = None
    
    # We can't render this error because we did not find a suiting template.
    if template is None:
      return None
    
    # Render template
    return template.render(**params)
  
  def _relativeize(self, filename):
    '''return the portion of a filename that is 'relative' to the directories in this lookup.'''
    filename = posixpath.normpath(filename)
    for dn in self.directories:
      if filename[0:len(dn)] == dn:
        return filename[len(dn):]
    else:
      return None
  
  def _load(self, filename, uri, text=None):
    try:
      if filename is not None:
        filename = posixpath.normpath(filename)
      
      encoding_errors = 'replace'
      if len(uri) > 4 and (uri[-5:].lower() == '.html' or uri[-4:].lower() == '.xml'):
        encoding_errors='htmlentityreplace'
      
      self.instances[uri] = Template(
          uri               = uri,
          filename          = filename,
          text              = text,
          lookup            = self,
          module_filename   = None,
          format_exceptions = self.format_template_exceptions,
          input_encoding    = 'utf-8',
          output_encoding   = smisk.mvc.Response.charset,
          encoding_errors   = encoding_errors,
          cache_type        = self.cache_type,
          default_filters   = ['unicode'],
          imports           = self.imports)
      if log.level <= logging.DEBUG and self.cache_type != 'file':
        code = self.instances[uri].code
        log.debug("Compiled %s into %d bytes of python code:\n%s", uri, len(code), code)
      return self.instances[uri]
    except:
      self.instances.pop(uri, None)
      raise
  
  def _check(self, uri, template):
    if template.filename is None:
      return template
    if not os.access(template.filename, os.F_OK):
      self.instances.pop(uri, None)
      raise exceptions.TemplateLookupException("Can't locate template for uri '%s'" % uri)
    elif template.module._modified_time < os.stat(template.filename)[stat.ST_MTIME]:
      self.instances.pop(uri, None)
      return self._load(template.filename, uri)
    else:
      return template
  
  def put_string(self, uri, text):
    raise NotImplementedError
  
  def put_template(self, uri, template):
    self.instances[uri] = template
  
