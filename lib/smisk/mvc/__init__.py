# encoding: utf-8
'''Model-View-Controller-based sub-framework.

This module and it's sub-modules constitutes the most common way of using
Smisk, mapping URLs to the *control tree* – an actual class tree, growing
from `control.Controller`.

**Key members**

* `main()` is a helper function which facilitates the most common use case:
  Setting up an application, configuring it, running it and logging uncaught
  exceptions.
  
* The `Application` class is the type of application. Normally you do not
  subclass `Application`, but rather configure it and its different
  components.
  
* The `console` module is an interactive console, aiding in development and
  management.

* The `control` module contains many useful functions for inspecting the
  *control tree*.


**Examples**::

  from smisk.mvc import *
  class root(Controller):
    def __call__(self, *args, **params):
      return {'message': 'Hello World!'}
  
  main()

'''
import sys, os, logging, mimetypes, codecs as char_codecs
import smisk.core

from smisk.core import app, request, response, URL
from smisk.config import config, LOGGING_FORMAT, LOGGING_DATEFMT
from smisk.mvc import http, control, model, filters
from smisk.serialization import serializers, Serializer
from smisk.util.cache import *
from smisk.util.collections import *
from smisk.util.DateTime import *
from smisk.util.introspect import *
from smisk.util.python import *
from smisk.util.string import *
from smisk.util.threads import *
from smisk.util.timing import *
from smisk.util.type import *
from smisk.mvc.template import Templates
from smisk.mvc.routing import Router, Destination
from smisk.mvc.decorators import *
from smisk.mvc.helpers import *

Controller = control.Controller
try:
  Entity = model.Entity
except ImportError:
  pass

log = logging.getLogger(__name__)

# MSIE error body sizes
_MSIE_ERROR_SIZES = { 400:512, 403:256, 404:512, 405:256, 406:512, 408:512,
                      409:512, 410:256, 500:512, 501:512, 505:512}

def environment():
  '''Name of the current environment.
  
  Returns the value of ``SMISK_ENVIRONMENT`` environment value and defaults to "``stable``".
  
  :rtype: string
  '''
  try:
    return os.environ['SMISK_ENVIRONMENT']
  except KeyError:
    return 'stable'


class Request(smisk.core.Request):
  serializer = None
  '''Serializer used for decoding request payload.
  '''


class Response(smisk.core.Response):
  format = None
  '''Any value which is a valid key of the serializers.extensions dict.
  '''
  
  serializer = None
  '''Serializer to use for encoding the response.
  '''
  
  fallback_serializer = None
  '''Last-resort serializer, used for error responses and etc.
  '''
  
  charset = 'utf-8'
  '''Character encoding used to encode the response body.
  :Deprecated: use Application.charset instead
  '''
  
  def adjust_status(self, has_content):
    '''Make sure 204 No Content is set for responses without content.
    '''
    p = self.find_header('Status:')
    if p != -1:
      if not has_content  and  self.headers[p][7:].strip().startswith('200'):
        self.headers[p] = 'Status: 204 No Content'
        self.remove_header('content-length:')
    elif not has_content:
      self.headers.append('Status: 204 No Content')
      self.remove_header('content-length:')
  
  
  def remove_header(self, name):
    '''Remove any instance of header named or prefixed *name*.
    '''
    name = name.lower()
    name_len = len(name)
    self.headers = [h for h in self.headers if h[:name_len].lower() != name]
  
  
  def remove_headers(self, *names):
    '''Remove any instance of headers named or prefixed *\*names*.
    '''
    for name in names:
      self.remove_header(name)
  
  
  def replace_header(self, header):
    '''Replace any instances of the same header type with *header*.
    '''
    name = header[:header.index(':')+1]
    self.remove_header(name)
    self.headers.append(header)
  
  
  def send_file(self, path):
    self.remove_header('content-location:')
    self.remove_header('vary:')
    if self.find_header('Content-Type') == -1:
      mt, menc = mimetypes.guess_type(path)
      if mt:
        if menc:
          mt = '%s;charset=%s' % (mt,menc)
        self.headers.append('Content-Type: %s' % mt)
    smisk.core.Response.send_file(self, path)
    self.begin()
  


class Application(smisk.core.Application):
  '''MVC application
  '''
  
  templates = None
  '''Templates handler
  '''
  
  routes = None
  '''Router
  '''
  
  serializer = None
  '''Used during runtime
  '''
  
  destination = None
  '''Used during runtime
  '''
  
  template = None
  '''Used during runtime
  '''
  
  unicode_errors = 'replace'
  '''How to handle unicode conversions
  '''
  
  def __init__(self, router=None, templates=None, *args, **kwargs):
    '''Initialize a new application
    '''
    super(Application, self).__init__(*args, **kwargs)
    self.request_class = Request
    self.response_class = Response
    
    if router is None:
      self.routes = Router()
    else:
      self.routes = router
    
    if templates is None and Templates.is_useable:
      self.templates = Templates()
    else:
      self.templates = templates
  
  
  def setup(self):
    '''Setup application state
    '''
    # Setup ETag
    etag = config.get('smisk.mvc.etag')
    if etag is not None and isinstance(etag, basestring):
      import hashlib
      config.set_default('smisk.mvc.etag', getattr(hashlib, etag))
    
    # Check templates config
    if self.templates:
      if not self.templates.directories:
        path = os.path.join(os.environ['SMISK_APP_DIR'], 'templates')
        if os.path.isdir(path):
          self.templates.directories = [path]
          log.debug('Using template directories: %s', ', '.join(self.templates.directories))
        else:
          log.info('Template directory not found -- disabling templates.')
          self.templates.directories = []
          self.templates = None
      if self.templates and not config.has_key('smisk.mvc.template.autoreload'):
        config.set_default('smisk.mvc.template.autoreload', config.get('smisk.autoreload.enable'))
    
    # Set fallback serializer
    if isinstance(Response.fallback_serializer, basestring):
      Response.fallback_serializer = serializers.find(Response.fallback_serializer)
    if Response.fallback_serializer not in serializers:
      # Might have been unregistered and need to be reconfigured
      Response.fallback_serializer = None
    if Response.fallback_serializer is None:
      try:
        Response.fallback_serializer = serializers.extensions['html']
      except KeyError:
        try:
          Response.fallback_serializer = serializers[0]
        except IndexError:
          Response.fallback_serializer = None
    
    # Create tables if needed and setup any models
    if model.metadata.bind:
      model.setup_all(True)
  
  
  def application_will_start(self):
    # Setup logging
    # Calling basicConfig has no effect if logging is already configured.
    # (for example by an application configuration)
    logging.basicConfig(format=LOGGING_FORMAT, datefmt=LOGGING_DATEFMT)
    
    # Call setup()
    self.setup()
    
    # Configure routers
    if isinstance(self.routes, Router):
      self.routes.configure()
    
    # Initialize mime types module
    mimetypes.init()
    
    # Register model.cleanup_all in atexit
    if model.metadata.bind:
      import atexit
      atexit.register(model.cleanup_all)
    
    # Info about serializers
    if log.level <= logging.DEBUG:
      log.debug('installed serializers: %s', ', '.join(unique_sorted_modules_of_items(serializers)) )
      log.debug('acceptable media types: %s', ', '.join(serializers.media_types.keys()))
      log.debug('available filename extensions: %s', ', '.join(serializers.extensions.keys()))
    
    # When we return, accept() in smisk.core is called
    log.info('Accepting connections')
  
  
  def application_did_stop(self):
    smisk.core.unbind()
  
  
  def _serializer_for_request_path_ext(self, fallback=None):
    '''
    Returns a serializer if the requests included a filename extension.
    Returns None if the requests did NOT include a filename extension.
    If fallback is set,
      Returns fallback if the requests included a filename extension that
      does not correspond to any available serializer.
    If fallback is NOT set,
      raises http.NotFound
    '''
    if self.response.format is None and self.request.url.path.rfind('.') != -1:
      filename = os.path.basename(self.request.url.path)
      p = filename.rfind('.')
      if p != -1:
        self.request.url.path = strip_filename_extension(self.request.url.path)
        self.response.format = filename[p+1:].lower()
        if log.level <= logging.DEBUG:
          log.debug('response format %r deduced from request filename extension', 
            self.response.format)
    if self.response.format is not None:
      try:
        return serializers.extensions[self.response.format]
      except KeyError:
        if fallback is not None:
          return fallback
        else:
          raise http.NotFound('Resource not available as %r' % self.response.format)
  
  
  def response_serializer(self, no_http_exc=False):
    '''
    Return the most appropriate serializer for handling response encoding.
    
    :param no_http_exc: If true, HTTP statuses are never rised when no acceptable 
                        serializer is found. Instead a fallback serializer will be returned:
                        First we try to return a serializer for format html, if that
                        fails we return the first registered serializer. If that also
                        fails there is nothing more left to do but return None.
                        Primarily used by `error()`.
    :type  no_http_exc: bool
    :return: The most appropriate serializer
    :rtype:  Serializer
    '''
    # Overridden by explicit response.format?
    if self.response.format is not None:
      # Should fail if not exists
      return serializers.extensions[self.response.format]
    
    # Overridden internally by explicit Content-Type header?
    p = self.response.find_header('Content-Type:')
    if p != -1:
      content_type = self.response.headers[p][13:].strip("\t ").lower()
      p = content_type.find(';')
      if p != -1:
        content_type = content_type[:p].rstrip("\t ")
      try:
        return serializers.media_types[content_type]
      except KeyError:
        if no_http_exc:
          return Response.fallback_serializer
        else:
          raise http.InternalServerError('Content-Type response header is set to type %r '\
            'which does not have any valid serializer associated with it.' % content_type)
    
    # Try filename extension
    fallback = None
    if no_http_exc:
      fallback = Response.fallback_serializer
    serializer = self._serializer_for_request_path_ext(fallback=fallback)
    if serializer is not None:
      return serializer
    
    # Try media type
    accept_types = self.request.env.get('HTTP_ACCEPT', None)
    if accept_types is not None and len(accept_types):
      if log.level <= logging.DEBUG:
        log.debug('Client accepts: %r', accept_types)
      
      # Parse the qvalue header
      tqs, highqs, partials, accept_any = parse_qvalue_header(accept_types, '*/*', '/*')
      
      # If the default serializer exists in the highest quality accept types, return it
      if Response.serializer is not None:
        for t in Response.serializer.media_types:
          if t in highqs:
            return Response.serializer
      
      # Find a serializer matching any accept type, ordered by qvalue
      available_types = serializers.media_types.keys()
      for tq in tqs:
        t = tq[0]
        if t in available_types:
          return serializers.media_types[t]
      
      # Accepts */* which is far more common than accepting partials, so we test this here
      # and simply return Response.serializer if the client accepts anything.
      if accept_any:
        if Response.serializer is not None:
          return Response.serializer
        else:
          return Response.fallback_serializer
      
      # If the default serializer matches any partial, return it (the likeliness of 
      # this happening is so small we wait until now)
      if Response.serializer is not None:
        for t in Response.serializer.media_types:
          if t[:t.find('/', 0)] in partials:
            return Response.serializer
      
      # Test the rest of the partials
      for t, serializer in serializers.media_types.items():
        if t[:t.find('/', 0)] in partials:
          return serializer
      
      # If an Accept header field is present, and if the server cannot send a response which 
      # is acceptable according to the combined Accept field value, then the server SHOULD 
      # send a 406 (not acceptable) response. [RFC 2616]
      log.info('Client demanded content type(s) we can not respond in. "Accept: %s"', accept_types)
      if config.get('smisk.mvc.strict_tcn', True):
        raise http.NotAcceptable()
    
    # The client did not ask for any type in particular
    
    # Strict TCN
    if Response.serializer is None:
      if no_http_exc or len(serializers) < 2:
        return Response.fallback_serializer
      else:
        raise http.MultipleChoices(self.request.url)
      
    # Return the default serializer
    return Response.serializer
  
  
  def parse_request(self):
    '''
    Parses the request, involving appropriate serializer if needed.
    
    :returns: (list arguments, dict parameters)
    :rtype:   tuple
    '''
    args = []
    log.debug('parsing request')
    
    # Set params to the query string
    params = self.request.get
    for k,v in params.iteritems():
      if isinstance(v, str):
        v = v.decode('utf-8', self.unicode_errors)
      params[k.decode('utf-8', self.unicode_errors)] = v
    
    # Look at Accept-Charset header and set self.response.charset accordingly
    accept_charset = self.request.env.get('HTTP_ACCEPT_CHARSET', False)
    if accept_charset:
      cqs, highqs, partials, accept_any = parse_qvalue_header(accept_charset.lower(),
                                            '*', None, self.response.charset)
      # If the charset we have already set is not in highq, use the first usable encoding
      if cqs is not True:
        alt_cs = None
        for cq in cqs:
          c = cq[0]
          try:
            char_codecs.lookup(c)
            alt_cs = c
            break
          except LookupError:
            pass
        
        if alt_cs is not None:
          self.response.charset = alt_cs
        else:
          # If an Accept-Charset header is present, and if the server cannot send a response 
          # which is acceptable according to the Accept-Charset header, then the server 
          # SHOULD send an error response with the 406 (not acceptable) status code, though 
          # the sending of an unacceptable response is also allowed. [RFC 2616]
          log.info('Client demanded charset(s) we can not respond using. "Accept-Charset: %s"',
            accept_charset)
          if config.get('smisk.mvc.strict_tcn', True):
            raise http.NotAcceptable()
        
        if log.level <= logging.DEBUG:
          log.debug('Using alternate response character encoding: %r (requested by client)',
            self.response.charset)
    
    # Parse body if POST request
    if self.request.method in ('POST', 'PUT'):
      
      path_ext_serializer = self._serializer_for_request_path_ext()
      if path_ext_serializer is None:
        content_type = self.request.env.get('CONTENT_TYPE', '').lower()
      else:
        content_type = path_ext_serializer.media_types[0]
      
      if content_type == 'application/x-www-form-urlencoded' or len(content_type) == 0:
        # Standard urlencoded content
        params.update(self.request.post)
      elif not content_type.startswith('multipart/'):
        # Multiparts are parsed by smisk.core, so let's try to
        # decode the body only if it's of another type.
        try:
          if path_ext_serializer is not None:
            self.request.serializer = path_ext_serializer
          else:
            self.request.serializer = serializers.media_types[content_type]
          log.debug('decoding request payload using %s', self.request.serializer)
          content_length = int(self.request.env.get('CONTENT_LENGTH', -1))
          (eargs, eparams) = self.request.serializer.unserialize(self.request.input, content_length)
          if eargs is not None:
            args.extend(eargs)
          if eparams is not None:
            params.update(eparams)
        except KeyError:
          log.error('Unable to parse request -- no serializer able to decode %r', content_type)
          raise http.UnsupportedMediaType()
    
    return (args, params)
  
  
  def apply_leaf_restrictions(self):
    '''Applies any restrictions set by the current leaf/destination.
    
    :rtype: None
    '''
    # Method restrictions
    try:
      log.debug('applying method restrictions for leaf %r', self.destination.leaf)
      leaf_methods = self.destination.leaf.methods
      method = self.request.method
      log.debug('leaf allows %r, request is %r', leaf_methods, method)
      
      if leaf_methods is not None:
        method_not_allowed = method not in leaf_methods
        is_opts_and_refl = (method == 'OPTIONS'  and  control.enable_reflection)
        
        if method_not_allowed  and  method == 'HEAD' and 'GET' in leaf_methods:
          # HEAD is always allowed as long as GET is allowed.
          # We perform the check here in order to give the user the possibility
          # to explicitly @expose a leaf with OPTIONS included in the methods 
          # argument. (Same reason with OPTIONS further down here)
          method_not_allowed = False
        elif method_not_allowed  or  method == 'OPTIONS':
          # HTTP 1.1 requires us to specify allowed methods in a 405 response
          # and we should also include Allow for OPTIONS requests.
          if is_opts_and_refl and method_not_allowed:
            # OPTIONS was not in leaf_methods, so add it through copy (not appending)
            leaf_methods = leaf_methods + ['OPTIONS']
          if 'HEAD' not in leaf_methods  and  'GET' in leaf_methods:
            # HEAD was not in leaf_methods, but GET is, so add it through copy (not appending)
            leaf_methods = leaf_methods + ['HEAD']
          self.response.headers.append('Allow: ' + ', '.join(leaf_methods))
        
        if method_not_allowed:
          # If OPTIONS request and control.enable_reflection is True, respond
          # with leaf relfection. Placing the check here, inside method_not_allowed,
          # allows the application designer to explicitly @expose a leaf with
          # OPTIONS included in the methods argument, in order for her to handle
          # a OPTIONS request, rather than Smisk taking over.
          if is_opts_and_refl:
            class LeafReflectionDestination(Destination):
              def _call_leaf(self, *args, **params):
                return control.leaf_reflection(self.leaf)
            self.destination = LeafReflectionDestination(self.destination.leaf)
          else:
            # Method not allowed
            raise http.MethodNotAllowed("The requested method %s is not allowed for the URI %s." %\
              (method, self.request.url.uri))
    except AttributeError:
      # self.destination.leaf does not have any method restrictions
      pass
    
    # Format restrictions
    try:
      leaf_formats = self.destination.leaf.formats
      for ext in self.response.serializer.extensions:
        if ext not in leaf_formats:
          self.response.serializer = None
          break
      if self.response.serializer is None:
        log.warn('client requested a response type which is not available for the current leaf')
        if self.response.format is not None:
          raise http.NotFound('Resource not available as %r' % self.response.format)
        elif config.get('smisk.mvc.strict_tcn', True) or len(leaf_formats) == 0:
          raise http.NotAcceptable()
        else:
          try:
            self.response.serializer = serializers.extensions[leaf_formats[0]]
          except KeyError:
            raise http.NotAcceptable()
    except AttributeError:
      # self.destination.leaf.formats does not exist -- no restrictions apply
      pass
  
  
  def call_leaf(self, args, params):
    '''
    Resolves and calls the appropriate leaf, passing args and params to it.
    
    :returns: Response structure or None
    :rtype:   dict
    '''
    # Add Content-Location response header if data encoding was deduced through
    # TCN or requested with a non-standard URI. (i.e. "/hello" instead of "/hello/")
    canonical_uri = self.destination.uri
    if self.response.serializer and (\
          not self.response.format \
        or \
          (canonical_uri and canonical_uri != self.request.url.path)\
        ):
      if canonical_uri:
        self.response.headers.append('Content-Location: %s.%s' % \
          (canonical_uri, self.response.serializer.extensions[0]))
      # Always add the vary header, because we do (T)CN
      self.response.headers.append('Vary: Accept-Charset, Accept')
    else:
      # Always add the vary header, because we do (T)CN. Here we know this
      # request does not negotiate accept type, as response type was explicitly
      # set by the client, so we do not include "accept".
      self.response.headers.append('Vary: Accept-Charset')
    
    # Call leaf
    if log.level <= logging.DEBUG:
      log.debug('Calling destination %r with args %r and params %r', self.destination, args, params)
    try:
      for filter in self.destination.leaf.filters:
        args, params = filter.before(*args, **params)
      rsp = self.destination(*args, **params)
      for filter in self.destination.leaf.filters:
        rsp = filter.after(rsp, *args, **params)
      return rsp
    except AttributeError:
      return self.destination(*args, **params)
  
  
  def encode_response(self, rsp):
    '''Encode the response object `rsp`
    
    :Returns: `rsp` encoded as a series of bytes
    :see: `send_response()`
    '''
    # No response body
    if rsp is None:
      if self.template:
        return self.template.render_unicode().encode(self.response.charset, self.unicode_errors)
      elif self.response.serializer and self.response.serializer.handles_empty_response:
        self.response.charset, rsp = self.response.serializer.serialize(rsp, self.response.charset)
        return rsp
      return None
    
    # If rsp is already a string, we do not process it further
    if isinstance(rsp, basestring):
      if isinstance(rsp, unicode):
        rsp = rsp.encode(self.response.charset, self.unicode_errors)
      return rsp
    
    # Make sure rsp is a dict
    assert isinstance(rsp, dict), 'controller leafs must return a dict, a string or None'
    
    # Use template as serializer, if available
    if self.template:
      for k,v in rsp.items():
        if isinstance(k, unicode):
          k2 = k.encode(self.template.input_encoding, self.unicode_errors)
          del rsp[k]
          rsp[k2] = v
      return self.template.render_unicode(**rsp).encode(
        self.response.charset, self.unicode_errors)
    
    # If we do not have a template, we use a data serializer
    self.response.charset, rsp = self.response.serializer.serialize(rsp, self.response.charset)
    return rsp
  
  
  def send_response(self, rsp):
    '''Send the response to the current client, finalizing the current HTTP
    transaction.
    '''
    # Empty rsp
    if rsp is None:
      # The leaf might have sent content using low-level functions,
      # so we need to confirm the response has not yet started and 
      # a custom content length header has not been set.
      if not self.response.has_begun:
        self.response.adjust_status(False)
      return
    
    # Add headers if the response has not yet begun
    if not self.response.has_begun:
      # Add Content-Length header
      if self.response.find_header('Content-Length:') == -1:
        self.response.headers.append('Content-Length: %d' % len(rsp))
      # Add Content-Type header
      self.response.serializer.add_content_type_header(self.response, self.response.charset)
      # Has content or not?
      if len(rsp) > 0:
        # Make sure appropriate status is set, if needed
        self.response.adjust_status(True)
        # Add ETag if enabled
        etag = config.get('smisk.mvc.etag')
        if etag is not None and self.response.find_header('ETag:') == -1:
          h = etag(''.join(self.response.headers))
          h.update(rsp)
          self.response.headers.append('ETag: "%s"' % h.hexdigest())
      else:
        # Make sure appropriate status is set, if needed
        self.response.adjust_status(False)
    
    # Debug print
    if log.level <= logging.DEBUG:
      self._log_debug_sending_rsp(rsp)
    
    # Send headers
    self.response.begin()
    
    # Head does not contain a payload, but all the headers should be exactly
    # like they would with a GET. (Including Content-Length)
    if self.request.method != 'HEAD':
      # Send body
      assert isinstance(rsp, str)
      self.response.write(rsp)
  
  
  def service(self):
    '''Manages the life of a HTTP transaction.
    '''
    if log.level <= logging.INFO:
      timer = Timer()
      log.info('Serving %s for client %s', request.url, request.env.get('REMOTE_ADDR','?'))
    
    # Reset pre-transaction properties
    self.request.serializer = None
    self.response.format = None
    self.response.serializer = None
    self.response.charset = self.charset
    self.destination = None
    self.template = None
    
    # Aquire response serializer.
    # We do this here already, because if response_serializer() raises and
    # exception, we do not want any leaf to be performed. If we would do this
    # after calling an leaf, chances are an important answer gets replaced by
    # an error response, like 406 Not Acceptable.
    self.response.serializer = self.response_serializer()
    if self.response.serializer.charset is not None:
      self.response.charset = self.response.serializer.charset
    
    # Parse request (and decode if needed)
    req_args, req_params = self.parse_request()
    
    # Option request for server in general?
    # The "/*" is an extension from Smisk. Most host servers respond to "*" themselves,
    # without asking Smisk.
    if self.request.method == 'OPTIONS' and \
    (self.request.env.get('SCRIPT_NAME') == '*' or self.request.url.path == '/*'):
      return self.service_server_OPTIONS(req_args, req_params)
      
    # Resolve route to destination
    self.destination, req_args, req_params = \
      self.routes(self.request.method, self.request.url, req_args, req_params)
    
    # Adjust formats if required by destination
    self.apply_leaf_restrictions()
    
    # Call the leaf which might generate a response object: rsp
    if model.metadata.bind:
      try:
        try:
          rsp = self.call_leaf(req_args, req_params)
          model.session.commit()
        except http.HTTPExc, e:
          if not e.status.is_error:
            log.debug('committing model transaction before handling non-error http status')
            model.session.commit()
          else:
            log.debug('rolling back model transaction')
            model.session.rollback()
          raise
        except:
          log.debug('rolling back model transaction')
          model.session.rollback()
          raise
      finally:
        model.session.remove()
    else:
      rsp = self.call_leaf(req_args, req_params)
  
    # Aquire template, if any
    if self.template is None and self.templates is not None:
      template_path = self.destination.template_path
      if template_path:
        self.template = self.template_for_path(os.path.join(*template_path))
  
    # Encode response
    rsp = self.encode_response(rsp)
    
    # Return a response to the client and thus completing the transaction.
    self.send_response(rsp)
    
    # Report performance
    if log.level <= logging.INFO:
      timer.finish()
      uri = None
      if self.destination is not None:
        uri = '%s.%s' % (self.destination.uri, self.response.serializer.extensions[0])
      else:
        uri = self.request.url.uri
      log.info('Processed %s in %.3fms', uri, timer.time()*1000.0)
  
  
  def service_server_OPTIONS(self, args, params):
    '''Handle a OPTIONS /* request
    '''
    log.info('servicing OPTIONS /*')
    self.response.replace_header('Allow: OPTIONS, GET, HEAD, POST, PUT, DELETE')
    rsp = None
    
    # Include information about this Smisk service, if enabled
    if control.enable_reflection:
      ctrl = control.Controller()
      rsp = {
        'methods': ctrl.smisk_methods(),
        'charsets': ctrl.smisk_charsets(),
        'serializers': ctrl.smisk_serializers()
      }
    
      # Encode response
      rsp = self.encode_response(rsp)
    
    # Return a response to the client and thus completing the transaction.
    self.send_response(rsp)
  
  
  def template_for_path(self, path):
    '''Aquire template for `path`.
    :rtype: template.Template
    '''
    return self.template_for_uri(self.template_uri_for_path(path))
  
  
  def template_uri_for_path(self, path):
    '''Get template URI for `path`.
    '''
    return path + '.' + self.response.serializer.extensions[0]
  
  
  def template_for_uri(self, uri):
    '''Aquire template for `uri`.
    :rtype: template.Template
    '''
    if log.level <= logging.DEBUG:
      log.debug('Looking for template %s', uri)
    return self.templates.template_for_uri(uri, exc_if_not_found=False)
  
  def _log_debug_sending_rsp(self, rsp):
    _body = ''
    if rsp:
      _body = '<%d bytes>' % len(rsp)
    log.debug('Sending response to %s: %r', self.request.env.get('REMOTE_ADDR','?'),
      '\r\n'.join(self.response.headers) + '\r\n\r\n' + _body)
  
  def _pad_rsp_for_msie(self, status_code, rsp):
    '''Get rid of MSIE "friendly" error messages
    '''
    if self.request.env.get('HTTP_USER_AGENT','').find('MSIE') != -1:
      # See: http://support.microsoft.com/kb/q218155/
      ielen = _MSIE_ERROR_SIZES.get(status_code, 0)
      if ielen:
        ielen += 1
        blen = len(rsp)
        if blen < ielen:
          log.debug('Adding additional body content for MSIE')
          rsp = rsp + (' ' * (ielen-blen))
    return rsp
  
  def error(self, extyp, exval, tb):
    '''Handle an error and produce an appropriate response.
    '''
    try:
      status = getattr(exval, 'status', http.InternalServerError)
      if not isinstance(status, http.Status):
        status = http.InternalServerError
      params = {}
      rsp = None
      
      # Log
      if status.is_error:
        log.error('%d Request failed for %r', status.code, self.request.url.path, 
          exc_info=(extyp, exval, tb))
        # Reset headers
        self.response.headers = []
      else:
        log.info('Non-200 HTTP status %s: %s for uri %r', extyp.__name__, exval, 
          self.request.url.uri)
        # Filter headers
        self.response.remove_headers('status:', 'vary:')
      
      # Set headers
      self.response.headers.extend([
        'Status: %s' % status,
        'Vary: Accept, Accept-Charset'
      ])
      
      # Set params
      params['name'] = unicode(status.name)
      params['code'] = getattr(exval, 'code', 0)
      try:
        params['code'] = int(params['code'])
      except ValueError:
        params['code'] = 0
      params['server'] = u'%s at %s' %\
        (self.request.env['SERVER_SOFTWARE'], self.request.env['SERVER_NAME'])
      
      # Include traceback if enabled
      if self.show_traceback:
        params['traceback'] = format_exc((extyp, exval, tb))
      else:
        params['traceback'] = None
      
      # HTTP exception has a bound leaf we want to call
      if isinstance(exval, http.HTTPExc):
        status_service_rsp = exval(self)
        if isinstance(status_service_rsp, StringType):
          rsp = status_service_rsp
        elif status_service_rsp:
          assert isinstance(status_service_rsp, DictType)
          params.update(status_service_rsp)
      if not params.get('description', False):
        params['description'] = unicode(getattr(exval, 'message', exval))
      
      # Service the error
      self.error_service(status, rsp, (extyp, exval, tb), params)
      
      return # We're done
    except:
      log.error('Failed to encode error', exc_info=1)
    log.error('Request failed for %r', self.request.url.path, exc_info=(extyp, exval, tb))
    super(Application, self).error(extyp, exval, tb)
  
  
  def error_service(self, status, rsp, exc_info, params):
    # Ony perform the following block if status type has a body and if
    # status_service_rsp did not contain a complete response body.
    if status.has_body:
      if rsp is None:
        # Try to use a serializer
        if self.response.serializer is None:
          # In this case an error occured very early.
          self.response.serializer = Response.fallback_serializer
          log.info('Responding using fallback serializer %s' % self.response.serializer)
        
        # Set format if a serializer was found
        format = self.response.serializer.extensions[0]
        
        # Try to use a template...
        if status.uses_template and self.templates:
          rsp = self.templates.render_error(status, params, format)
        
        # ...or a serializer
        if rsp is None:
          self.response.charset, rsp = self.response.serializer.serialize_error(
            status, params, self.response.charset)
      
      # MSIE body length fix
      rsp = self._pad_rsp_for_msie(status.code, rsp)
    else:
      rsp = ''
    
    # Set standard headers
    if not self.response.has_begun:
      if self.response.serializer:
        self.response.serializer.add_content_type_header(self.response, self.response.charset)
      self.response.replace_header('Content-Length: %d' % len(rsp))
      self.response.replace_header('Cache-Control: no-cache')
    
    # Send response
    if log.level <= logging.DEBUG:
      self._log_debug_sending_rsp(rsp)
    self.response.write(rsp)


#---------------------------------------------------------------------------
# Configuration filter
# Some things must be accessed as fast as possible, thus this filter

def smisk_mvc(conf):
  # Response.serializer
  if 'smisk.mvc.response.serializer' in conf:
    Response.serializer = conf['smisk.mvc.response.serializer']
    if Response.serializer is not None and not isinstance(Response.serializer, Serializer):
      try:
        Response.serializer = serializers.extensions[Response.serializer]
        log.debug('configured smisk.mvc.Response.serializer=%r', Response.serializer)
      except KeyError:
        log.error('configuration of smisk.mvc.Response.serializer failed: '\
          'No serializer named %r', Response.serializer)
        Response.serializer = None
  
  # Application.show_traceback
  if 'smisk.mvc.show_traceback' in conf:
    Application.show_traceback = conf['smisk.mvc.show_traceback']
  
  # Initialize routes
  a = Application.current
  if a and isinstance(a.routes, Router):
    a.routes.configure()

config.add_filter(smisk_mvc)
del smisk_mvc


#---------------------------------------------------------------------------
# A version of the Main helper which updates SMISK_ENVIRONMENT and calls
# Application.setup() in Main.setup()

import smisk.util.main

class Main(smisk.util.main.Main):
  default_app_type = Application
  
  def setup(self, application=None, appdir=None, *args, **kwargs):
    if self._is_set_up:
      return smisk.core.Application.current
    
    application = super(Main, self).setup(application=application, appdir=appdir, *args, **kwargs)
    
    os.environ['SMISK_ENVIRONMENT'] = environment()
    application.setup()
    
    return application

main = Main()

# For backwards compatibility
setup = main.setup
run = main.run
