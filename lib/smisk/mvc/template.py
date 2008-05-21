# lookup.py
# Copyright (C) 2006, 2007, 2008 Michael Bayer mike_mp@zzzcomputing.com
#
# This module is part of Mako and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php
#
# Modified for the Smisk project by Rasmus Andersson.

import os, sys, stat, posixpath, re, logging
from mako import exceptions, util
from mako.template import Template
from . import http

log = logging.getLogger(__name__)

try:
  import threading
except:
  import dummy_threading as threading

exceptions.TopLevelLookupException.http_code = 404

class Templates(object):
  def __init__(self, app):
    self.app = app
    self.directories = []
    self.errors = {}
    self.autoreload = None # will be assigned app.autoreload by app if None after configuration
    self.default_locals = {}
    self._cache_lock = threading.Lock()
    self.show_traceback = True
    
    self.cache_type = 'memory'
    self.cache_limit = -1
    self.imports = [
      'import os, sys, time, logging',
      'from smisk.mvc import app, request, response',
      'log = logging.getLogger(\'view:\' + _template_uri)'
    ]
    # for compat with mako
    self.get_template = self.template_for_uri
  
  def reload_config(self):
    if self.cache_limit == -1:
      self._collection = {}
      self._uri_cache = {}
    else:
      self._collection = util.LRUCache(self.cache_limit)
      self._uri_cache = util.LRUCache(self.cache_limit)
  
  def template_for_uri(self, uri):
    try:
      if self.autoreload:
        return self._check(uri, self._collection[uri])
      else:
        return self._collection[uri]
    except KeyError:
      u = re.sub(r'^\/+', '', uri)
      for dn in self.directories:
        srcfile = posixpath.normpath(posixpath.join(dn, u))
        if os.access(srcfile, os.F_OK):
          return self._load(srcfile, uri)
      else:
        raise exceptions.TopLevelLookupException("Cant locate template for uri '%s'" % uri)
  
  def builtin_error_template(self):
    if '_builtin_error_' in self._collection:
      return self._collection['_builtin_error_']
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
    self._cache_lock.acquire()
    try:
      try:
        # try returning from collection one more time in case concurrent thread already loaded
        return self._collection[uri]
      except KeyError:
        pass
      try:
        if filename is not None:
          filename = posixpath.normpath(filename)
        self._collection[uri] = Template(
          uri=uri,
          filename=filename,
          text=text,
          lookup=self,
          module_filename=None,
          format_exceptions=False,
          input_encoding=self.app.input_encoding,
          output_encoding=self.app.output_encoding,
          cache_type=self.cache_type,
          default_filters=['str'],
          #default_filters=['unicode'],
          imports=self.imports)
        if __debug__ and self.cache_type != 'file':
          log.debug("Compiled %s into:\n%s", uri, self._collection[uri].code.strip())
        return self._collection[uri]
      except:
        self._collection.pop(uri, None)
        raise
    finally:
      self._cache_lock.release()
  
  def _check(self, uri, template):
    if template.filename is None:
      return template
    if not os.access(template.filename, os.F_OK):
      self._collection.pop(uri, None)
      raise exceptions.TemplateLookupException("Cant locate template for uri '%s'" % uri)
    elif template.module._modified_time < os.stat(template.filename)[stat.ST_MTIME]:
      self._collection.pop(uri, None)
      return self._load(template.filename, uri)
    else:
      return template
  
  def put_string(self, uri, text):
    raise NotImplementedError
  
  def put_template(self, uri, template):
    self._collection[uri] = template
  

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