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

:requires: mako
'''
import os, sys, stat, posixpath, re, logging
import smisk.core.xml
from smisk.core import URL
from smisk.config import config
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
  mako.filters.url_escape = URL.escape
  mako.filters.url_unescape = URL.decode
except ImportError:
  # mako is not installed
  Template = None

__all__ = ['Templates', 'Template']
log = logging.getLogger(__name__)


class Templates(object):
  '''Templates.
  '''
  
  imports = [
    'import os, sys, time, logging',
    'from smisk.core import app, request, response',
    'from smisk.mvc.template.filters import j',
    'log = logging.getLogger(\'template:\' + _template_uri)'
  ]
  ''':type: list'''
  
  directories = None
  '''Directories in which to find templates.
  
  :type: list
  '''
  
  is_useable = Template is not None
  '''True if mako is installed and templating can be used'''
  
  def __init__(self):
    self.directories = []
    self.get_template = self.template_for_uri # for compat with mako
    self.reset_cache()
  
  def reset_cache(self):
    limit = config.get('smisk.mvc.template.cache_limit', -1)
    if limit == -1:
      self.instances = {}
      self._uri_cache = {}
    else:
      self.instances = LRUCache(limit)
      self._uri_cache = LRUCache(limit)
  
  def template_for_uri(self, uri, exc_if_not_found=True):
    '''
    :return: template for the uri provided 
    :rtype:  Template
    '''
    try:
      template = self.instances[uri]
      if config.get('smisk.mvc.template.autoreload'):
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
    errors = config.get('smisk.mvc.template.errors', {})
    if status.code in errors:
      template = self.template_for_uri('%s.%s' % (errors[status.code], format), False)
    elif status in errors:
      template = self.template_for_uri('%s.%s' % (errors[status], format), False)
    elif 0 in errors:
      template = self.template_for_uri('%s.%s' % (errors[0], format), False)
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
      
      cache_type = config.get('smisk.mvc.template.cache_type', 'memory')
      
      self.instances[uri] = Template(
          uri               = uri,
          filename          = filename,
          text              = text,
          lookup            = self,
          module_filename   = None,
          format_exceptions = config.get('smisk.mvc.template.format_exceptions', True),
          input_encoding    = config.get('smisk.mvc.template.input_encoding', 'utf-8'),
          output_encoding   = smisk.mvc.Response.charset,
          encoding_errors   = encoding_errors,
          cache_type        = cache_type,
          default_filters   = config.get('smisk.mvc.template.default_filters', ['unicode']),
          imports           = self.imports)
      if log.level <= logging.DEBUG and cache_type != 'file':
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
  
