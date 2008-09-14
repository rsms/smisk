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
from mako import exceptions, util
from mako.template import Template
from .. import http
from . import filters

log = logging.getLogger(__name__)
exceptions.TopLevelLookupException.http_code = 404

# Replace Mako filter with the faster Smisk implementations
mako.filters.html_escape = smisk.core.xml.escape
mako.filters.xml_escape = smisk.core.xml.escape
mako.filters.url_escape = URL.encode
mako.filters.url_unescape = URL.decode

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
  
  show_traceback = True
  '''
  Include stack traceback in error messages.
  
  :type: bool
  '''
  
  autoreload = None
  '''
  Automatically reload templates which has been modified.
  
  If this is set to None when `app` starts accepting requests, the application
  will set the value according to its own autoreload value.
  
  :type: bool
  '''
  
  directories = None
  '''
  Directories in which to find templates.
  
  :type: list
  '''
  
  errors = None
  ''':type: dict'''
  
  app = None
  ''':type: smisk.core.Application'''
  
  def __init__(self, app):
    self.app = app
    self.directories = []
    self.errors = {}
    self.get_template = self.template_for_uri # for compat with mako
    self.reset_cache()
  
  def reset_cache(self):
    if self.cache_limit == -1:
      self.instances = {}
      self._uri_cache = {}
    else:
      self.instances = util.LRUCache(self.cache_limit)
      self._uri_cache = util.LRUCache(self.cache_limit)
  
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
  
  def builtin_error_template(self):
    if '_builtin_error_' in self.instances:
      return self.instances['_builtin_error_']
    else:
      return self._load(filename=None, uri='_builtin_error_', text=HTML_ERROR_TEMPLATE)
  
  def adjust_uri(self, uri, relativeto):
    """adjust the given uri based on the calling filename."""
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
  
  def render_error(self, typ=None, val=None, tb=None):
    if typ is None:
      (typ, val, tb) = sys.exc_info()
    status = getattr(val, 'http_code', 500)
    data = dict(
      title=str(status),
      message=str(val),
      server_info = '%s at %s' % (self.app.request.env['SERVER_SOFTWARE'],
                                  self.app.request.env['SERVER_NAME']),
    )
    
    # Add HTTP status title
    if status in http.STATUS:
      data['title'] = '%d %s' % (status, http.STATUS[status])
    
    # Add traceback if enabled
    #if self.show_traceback:
    #  data['traceback'] = utils.format_exc((typ, val, tb))
    
    # Compile body from template
    body = ''
    template = None
    if status in self.errors:
      template = self.template_for_uri(self.errors[status])
    elif 0 in self.errors:
      template = self.template_for_uri(self.errors[0])
    else:
      return None
      #template = self.builtin_error_template()
    
    body = template.render(**data)
    
    # Get rid of MSIE "friendly" error messages
    if self.app.request.env.get('HTTP_USER_AGENT','').find('MSIE') != -1:
      # See: http://support.microsoft.com/kb/q218155/
      ielen = _msie_error_sizes.get(status, 0)
      if ielen:
        ielen += 1
        blen = len(body)
        if blen < ielen:
          log.debug('Adding additional body content for MSIE')
          body = body + (' ' * (ielen-blen))
    
    # Set headers
    self.app.response.headers = [
      'Status: %d' % status,
      'Content-Type: text/html',
      'Content-Length: %d' % len(body)]
    
    # Send response
    self.app.response.write(body)
    return True
  
  def _relativeize(self, filename):
    """return the portion of a filename that is 'relative' to the directories in this lookup."""
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
      self.instances[uri] = Template(
        uri=uri,
        filename=filename,
        text=text,
        lookup=self,
        module_filename=None,
        format_exceptions=False,
        #input_encoding=self.app.input_encoding,
        output_encoding=self.app.default_output_encoding,
        encoding_errors='replace',
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
  

HTML_ERROR_TEMPLATE = r'''
<%! from mako.exceptions import RichTraceback %>
<html>
<head>
    <title>${title|x}</title>
    <style>
        body { font-family:verdana; margin:10px 30px 10px 30px;}
        .stacktrace { margin:5px 5px 5px 5px; }
        .highlight { padding:0px 10px 0px 10px; background-color:#9F9FDF; }
        .nonhighlight { padding:0px; background-color:#DFDFDF; }
        .sample { padding:10px; margin:10px 10px 10px 10px; font-family:monospace; }
        .sampleline { padding:0px 10px 0px 10px; }
        .sourceline { margin:5px 5px 10px 5px; font-family:monospace;}
        .location { font-size:80%; }
    </style>
</head>
<body>
  <h1>${title|x}</h1>
  <%
      tback = RichTraceback()
      src = tback.source
      line = tback.lineno
      if src:
          lines = src.split('\n')
      else:
          lines = None
  %>
  <h3>${str(tback.error.__class__.__name__)}: ${str(tback.error)}</h3>

  % if lines:
      <div class="sample">
      <div class="nonhighlight">
  % for index in range(max(0, line-4),min(len(lines), line+5)):
      % if index + 1 == line:
  <div class="highlight">${index + 1} ${lines[index] | h}</div>
      % else:
  <div class="sampleline">${index + 1} ${lines[index] | h}</div>
      % endif
  % endfor
      </div>
      </div>
  % endif

  <div class="stacktrace">
  % for (filename, lineno, function, line) in tback.reverse_traceback:
      <div class="location">${filename}, line ${lineno}:</div>
      <div class="sourceline">${line | h}</div>
  % endfor
  </div>
  <address>${server_info}</address>
</body>
</html>
'''