# encoding: utf-8
# Based on lookup.py from the Mako project
# Copyright (C) 2006, 2007, 2008 Michael Bayer mike_mp@zzzcomputing.com
#
# This module is part of Mako and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php
#
# Modified for Smisk by Rasmus Andersson.
#
'''
Templating
'''
import os, sys, stat, posixpath, re, logging
import mako.filters, smisk.core.xml
from smisk.core import URL
from mako import exceptions
from mako.util import LRUCache
from mako.template import Template
from smisk.mvc import http
import filters
from smisk import util

log = logging.getLogger(__name__)
exceptions.TopLevelLookupException.status = http.NotFound

# Replace Mako filter with the faster Smisk implementations
mako.filters.html_escape = smisk.core.xml.escape
mako.filters.xml_escape = smisk.core.xml.escape
mako.filters.url_escape = URL.encode
mako.filters.url_unescape = URL.decode

# MSIE error body sizes
_msie_error_sizes = { 400:512, 403:256, 404:512, 405:256, 406:512, 408:512,
                      409:512, 410:256, 500:512, 501:512, 505:512}

class Templates(object):
  cache_limit = -1
  '''
  Limit cache size.
  
  0 means no cache.
  -1 means no limit.
  any positive value results in a LRU-approach.
  
  :type: int
  '''
  
  cache_type = 'memory'
  '''
  Type of cache.
  
  :type: string
  '''
  
  imports = [
    'import os, sys, time, logging',
    'from smisk.mvc import application, request, response',
    'from smisk.mvc.template.filters import j',
    'log = logging.getLogger(\'template:\' + _template_uri)'
  ]
  ''':type: list'''
  
  autoreload = None
  '''
  Automatically reload templates which has been modified.
  
  If this is set to None when `app` starts accepting requests, the application
  will set the value according to its own autoreload value.
  
  :type: bool
  '''
  
  format_template_exceptions = True
  '''
  Let the templating engine render information about template formatting exceptions.
  
  Things like missing or misspelled variables etc.
  
  :type: bool
  '''
  
  directories = None
  '''
  Directories in which to find templates.
  
  :type: list
  '''
  
  errors = {}
  '''
  Map http error to a template path.
  
  i.e. 500: 'errors/server_error'
  
  :type: dict
  '''
  
  app = None
  ''':type: smisk.core.Application'''
  
  def __init__(self, app):
    self.app = app
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
      if self.autoreload and template is not None:
        template = self._check(uri, template)
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
  
  def builtin_error_template(self, format='html'):
    cache_id = '__builtin_error.'+format
    if cache_id in self.instances:
      return self.instances[cache_id]
    elif format in ERROR_TEMPLATES:
      return self._load(filename=None, uri=cache_id, text=ERROR_TEMPLATES[format])
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
    rsp = template.render(**params)
    
    # Get rid of MSIE "friendly" error messages
    if self.app.request.env.get('HTTP_USER_AGENT','').find('MSIE') != -1:
      # See: http://support.microsoft.com/kb/q218155/
      ielen = _msie_error_sizes.get(status, 0)
      if ielen:
        ielen += 1
        blen = len(rsp)
        if blen < ielen:
          log.debug('Adding additional body content for MSIE')
          rsp = rsp + (' ' * (ielen-blen))
    
    return rsp
  
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
        uri=uri,
        filename=filename,
        text=text,
        lookup=self,
        module_filename=None,
        format_exceptions=self.format_template_exceptions,
        input_encoding='utf-8', # xxx todo: check file using Unicode BOM, #encoding:-patterns, etc.
        output_encoding=self.app.default_output_encoding,
        encoding_errors=encoding_errors,
        cache_type=self.cache_type,
        default_filters=['str'],
        #default_filters=['unicode'],
        imports=self.imports)
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
  

ERROR_TEMPLATES = {

'html': r'''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
  <head>
    <title>${title|x}</title>
    <style type="text/css">
      body,html { padding:0; margin:0; background:#666; }
      h1 { padding:25pt 10pt 10pt 15pt; background:#ffb2bf; color:#560c00; font-family:arial,helvetica,sans-serif; margin:0; }
      address, p { font-family:'lucida grande',verdana,arial,sans-serif; }
      p.message { padding:10pt 16pt; background:#fff; color:#222; margin:0; font-size:.9em; }
      pre.traceback { padding:10pt 15pt 25pt 15pt; line-height:1.4; background:#f2f2ca; color:#52523b; margin:0; border-top:1px solid #e3e3ba; border-bottom:1px solid #555; }
      hr { display:none; }
      address { padding:10pt 15pt; color:#333; font-size:11px; }
    </style>
  </head>
  <body>
    <h1>${title|x}</h1>
    <p class="message">${message|x}</p>
    % if traceback is not None:
    <pre class="traceback">${traceback|x}</pre>
    % endif
    <hr/>
    <address>${server_info|x}</address>
  </body>
</html>'''

}