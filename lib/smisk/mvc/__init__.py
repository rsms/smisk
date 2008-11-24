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
from smisk.mvc import http, control, model, filters
from smisk.serialization import serializers
from smisk.util.cache import *
from smisk.util.collections import *
from smisk.util.DateTime import *
from smisk.util.introspect import *
from smisk.util.python import *
from smisk.util.string import *
from smisk.util.threads import *
from smisk.util.timing import *
from smisk.util.type import *
from smisk.util.main import *
from smisk.mvc.template import Templates
from smisk.mvc.routing import Router
from smisk.mvc.decorators import *

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
  
  Any initial value has no effect.
  Available during a HTTP transaction.
  
  :type: smisk.serialization.Serializer
  '''


class Response(smisk.core.Response):
  format = None
  '''Any value which is a valid key of the serializers.extensions dict.
  
  Any initial value has no effect (replaced during runtime).
  
  :type: string
  '''
  
  serializer = None
  '''Serializer to use for encoding the response.
  
  The value of ``Response.serializer`` (class property value) serves as
  the application default serializer, used in cases where we need to encode 
  the response, but the client is not specific about which serializer to use.
  
  If None, strict `TCN <http://www.ietf.org/rfc/rfc2295.txt>`__ applies.
  
  :see: `fallback_serializer`
  :type: smisk.serialization.Serializer
  '''
  
  fallback_serializer = None
  '''Last-resort serializer, used for error responses and etc.
  
  If None when `Application.application_will_start` is called, this will
  be set to a HTML-serializer, and if none is available, simply the first
  registered serializer will be used.
  
  The class property is the only one used, the instance property has no 
  meaning and no effect, thus if you want to modify this during runtime,
  you should do this ``Response.fallback_serializer = my_serializer`` instead of
  this ``app.response.fallback_serializer = my_serializer``.
  
  :type: smisk.serialization.Serializer
  '''
  
  charset = 'utf-8'
  '''Character encoding used to encode the response body.
  
  The value of ``Response.charset`` (class property value) serves as
  the application default charset.
  
  :type: string
  '''
  
  def send_file(self, path):
    i = self.find_header('Content-Location')
    if i != -1:
      del self.headers[i]
    i = self.find_header('Vary')
    if i != -1:
      del self.headers[i]
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
  '''Templates handler.
  
  If this evaluates to false, templates are disabled.
  
  :see: `__init__()`
  :type: Templates
  '''
  
  routes = None
  '''Router.
  
  :type: Router
  '''
  
  autoreload = False
  ''':type: bool
  '''
  
  strict_tcn = True
  '''Controls whether or not this application is strict about
  transparent content negotiation.
  
  For example, if this is ``True`` and a client accepts a character
  encoding which is not available, a 206 Not Acceptable response is sent.
  If the value would have been ``False``, the response would be sent
  using a data encoder default character set.
  
  This affects ``Accept*`` request headers which demands can not be met.
  
  As HTTP 1.1 (RFC 2616) allows fallback to defaults (though not 
  recommended) we provide the option of turning off the 206 response.
  Setting this to false will cause Smisk to encode text responses using
  a best-guess character encoding.
  
  :type: bool
  '''
  
  etag = None
  '''
  Enables adding an ETag header to all buffered responses.
  
  The value needs to be either the name of a valid hash function in the
  ``hashlib`` module (i.e. "md5"), or a something respoding in the same way
  as the hash functions in hashlib. (i.e. need to return a hexadecimal
  string rep when::
  
    h = self.etag(data)
    h.update(more_data)
    etag_value = h.hexdigest()
  
  Enabling this is generally not recommended as it introduces a small to
  moderate performance hit, because a checksum need to be calculated for
  each response, and the nature of the data -- Smisk can not know exactly
  about all stakes in a transaction, thus constructing a valid ETag might
  somethimes be impossible.
  
  :type: object
  '''
  
  serializer = None
  '''
  Used during runtime.
  Here because we want to use it in error()
  
  :type: Serializer
  '''
  
  destination = None
  '''
  Used during runtime.
  Available in actions, serializers and templates.
  
  :type: smisk.mvc.routing.Destination
  '''
  
  template = None
  '''
  Used during runtime.
  
  :type: mako.template.Template
  '''
  
  unicode_errors = 'replace'
  '''How to handle unicode conversions.
  
  Possible values: ``strict, ignore, replace, xmlcharrefreplace, backslashreplace``
  
  :type: string
  '''
  
  def __init__(self,
               autoreload=False,
               etag=None, 
               router=None,
               templates=None,
               show_traceback=False,
               *args, **kwargs):
    '''Initialize a new application.
    '''
    super(Application, self).__init__(*args, **kwargs)
    self.request_class = Request
    self.response_class = Response
    
    self.etag = etag
    self.autoreload = autoreload
    self.show_traceback = show_traceback
    
    if router is None:
      self.routes = Router()
    else:
      self.routes = router
    
    if templates is None and Templates.is_useable:
      self.templates = Templates()
    else:
      self.templates = templates
  
  
  def autoload_configuration(self, config_mod_name='config'):
    '''Automatically load configuration from application sub-module named `config_mod_name`.
    
    :Parameters:
      config_mod_name : string
        Name of the application configuration sub-module
    :rtype: None
    '''
    import imp
    path = os.path.join(os.environ['SMISK_APP_DIR'], config_mod_name)
    locs = {'app': self}
    if os.path.isdir(path):
      # config/__init__.py
      execfile(os.path.join(path, '__init__.py'), globals(), locs)
      path = os.path.join(path, '%s.py' % environment())
      if os.path.isfile(path):
        # config/environment.py
        execfile(path, globals(), locs)
    elif os.path.isfile(path + '.py'):
      # config.py
      execfile(path + '.py', globals(), locs)
    elif os.path.isfile(path + '.pyc'):
      # config.pyc
      execfile(path + '.pyc', globals(), locs)
  
  
  def setup(self):
    '''Setup application state.
    
    Can be called multiple times and is automatically called, just after calling
    `autoload_configuration()`, by `smisk.mvc.setup()` and `application_will_start()`.
    
    **Outline**
    
    1. If `etag` is enabled and is a string, replaces `etag` with the named hashing
       algorithm from hashlib.
    2. If `templates` are enabled but ``templates.directories`` evaluates to false,
       set ``templates.directories`` to the default ``[SMISK_APP_DIR + "templates"]``.
    3. Make sure `Response.fallback_serializer` has a valid serializer as it's value.
    4. Setup any models.
    
    :rtype: None
    '''
    # Setup logging
    # Calling basicConfig has no effect if logging is already configured.
    # (for example by an application configuration)
    logging.basicConfig(format='%(levelname)-8s %(name)-20s %(message)s')
    
    # Setup ETag
    if self.etag is not None and isinstance(self.etag, basestring):
      import hashlib
      self.etag = getattr(hashlib, self.etag)
    
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
      if self.templates and self.templates.autoreload is None:
        self.templates.autoreload = self.autoreload
    
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
    
    # Setup any models
    model.setup_all()
  
  
  def application_will_start(self):
    # Call setup()
    self.setup()
    
    # Initialize mime types module
    mimetypes.init()
    
    # Info about serializers
    if log.level <= logging.DEBUG:
      log.debug('installed serializers: %s', ', '.join(unique_sorted_modules_of_items(serializers)) )
      log.debug('acceptable media types: %s', ', '.join(serializers.media_types.keys()))
      log.debug('available filename extensions: %s', ', '.join(serializers.extensions.keys()))
    
    # When we return, accept() in smisk.core is called
    log.info('Accepting connections')
  
  
  def application_did_stop(self):
    smisk.core.unbind()
    model.cleanup_all()
  
  
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
    if self.request.url.path.rfind('.') != -1:
      filename = os.path.basename(self.request.url.path)
      p = filename.rfind('.')
      if p != -1:
        self.request.url.path = strip_filename_extension(self.request.url.path)
        self.response.format = filename[p+1:].lower()
        if log.level <= logging.DEBUG:
          log.debug('Client asked for format %r', self.response.format)
        try:
          return serializers.extensions[self.response.format]
        except KeyError:
          if no_http_exc:
            return Response.fallback_serializer
          else:
            raise http.NotFound('Resource not available as %r' % self.response.format)
    
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
      if self.strict_tcn:
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
    
    # Set params to the query string
    params = self.request.get
    for k,v in params.iteritems():
      if isinstance(v, str):
        v = v.decode('utf-8', self.unicode_errors)
      params[k.decode('utf-8', self.unicode_errors)] = v
    
    # Look at Accept-Charset header and set self.response.charset accordingly
    accept_charset = self.request.env.get('HTTP_ACCEPT_CHARSET', False)
    if accept_charset:
      cqs, highqs, partials, accept_any = parse_qvalue_header(accept_charset.lower(), '*', None)
      # If the charset we have already set is not in highq, use the first usable encoding
      if self.response.charset not in highqs:
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
          if self.strict_tcn:
            raise http.NotAcceptable()
        
        if log.level <= logging.DEBUG:
          log.debug('Using alternate response character encoding: %r (requested by client)',
            self.response.charset)
    
    # Parse body if POST request
    if self.request.env['REQUEST_METHOD'] == 'POST':
      content_type = self.request.env.get('CONTENT_TYPE', '').lower()
      if content_type == 'application/x-www-form-urlencoded' or len(content_type) == 0:
        # Standard urlencoded content
        params.update(self.request.post)
      elif not content_type.startswith('multipart/'):
        # Multiparts are parsed by smisk.core, so let's only try to
        # decode the body if it's of another type.
        try:
          self.request.serializer = serializers.media_types[content_type]
          log.debug('decoding POST data using %s', self.request.serializer)
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
  
  
  def apply_action_format_restrictions(self):
    '''Applies any format restrictions set by the current action.
    
    :rtype: None
    '''
    try:
      action_formats = self.destination.action.formats
      for ext in self.response.serializer.extensions:
        if ext not in action_formats:
          self.response.serializer = None
          break
      if self.response.serializer is None:
        log.warn('client requested a response type which is not available for the current action')
        if self.response.format is not None:
          raise http.NotFound('Resource not available as %r' % self.response.format)
        elif self.strict_tcn or len(action_formats) == 0:
          raise http.NotAcceptable()
        else:
          try:
            self.response.serializer = serializers.extensions[action_formats[0]]
          except KeyError:
            raise http.NotAcceptable()
    except AttributeError:
      # self.destination.action.formats does not exist -- no restrictions apply
      pass
  
  
  def call_action(self, args, params):
    '''
    Resolves and calls the appropriate action, passing args and params to it.
    
    :returns: Response structure or None
    :rtype:   dict
    '''
    # Add Content-Location response header if data encoding was deduced through
    # TCN or requested with a non-standard URI. (i.e. "/hello" instead of "/hello/")
    if self.response.serializer and (\
          not self.response.format \
        or \
          (self.destination.uri and self.destination.uri != self.request.url.path)\
        ):
      self.response.headers.append('Content-Location: %s.%s' % \
        (self.destination.uri, self.response.serializer.extensions[0]))
      # Always add the vary header, because we do (T)CN
      self.response.headers.append('Vary: Accept-Charset, Accept')
    else:
      # Always add the vary header, because we do (T)CN. Here we know this
      # request does not negotiate accept type, as response type was explicitly
      # set by the client, so we do not include "accept".
      self.response.headers.append('Vary: Accept-Charset')
    
    # Call action
    if log.level <= logging.DEBUG:
      log.debug('Calling destination %r with args %r and params %r', self.destination, args, params)
    try:
      for filter in self.destination.action.filters:
        args, params = filter.before(*args, **params)
      rsp = self.destination(*args, **params)
      for filter in self.destination.action.filters:
        rsp = filter.after(rsp, *args, **params)
      return rsp
    except AttributeError:
      return self.destination(*args, **params)
  
  
  def encode_response(self, rsp):
    '''Encode the response object `rsp`
    
    :Parameters:
      rsp : object
        Must be a string, a dict or None
    :Returns:
      `rsp` encoded as a series of bytes
    :rtype: buffer
    :see: `send_response()`
    '''
    # No response body
    if rsp is None:
      if self.template:
        return self.template.render_unicode().encode(
          self.response.charset, self.unicode_errors)
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
    
    :Parameters:
      rsp : str
        Response body
    :rtype: None
    :see: `encode_response()`
    '''
    # Empty rsp
    if rsp is None:
      # The action might have sent content using low-level functions,
      # so we need to confirm the response has not yet started and 
      # a custom content length header has not been set.
      if not self.response.has_begun and self.response.find_header('Content-Length:') == -1:
        self.response.headers.append('Content-Length: 0')
      return
    
    # Add headers if the response has not yet begun
    if not self.response.has_begun:
      # Add Content-Length header
      if self.response.find_header('Content-Length:') == -1:
        self.response.headers.append('Content-Length: %d' % len(rsp))
      # Add Content-Type header
      self.response.serializer.add_content_type_header(self.response, self.response.charset)
      # Add ETag
      if self.etag is not None and len(rsp) > 0 and self.response.find_header('ETag:') == -1:
        h = self.etag(''.join(self.response.headers))
        h.update(rsp)
        self.response.headers.append('ETag: "%s"' % h.hexdigest())
    
    # Debug print
    if log.level <= logging.DEBUG:
      self._log_debug_sending_rsp(rsp)
    
    # Send body
    assert isinstance(rsp, str)
    self.response.write(rsp)
  
  
  def service(self):
    '''Manages the life of a HTTP transaction.
    
    **Summary**
    
    #. Reset current shared `request`, `response` and `self`.
    
    #. Aquire response serializer from `response_serializer()`.
    
       #. Try looking at ``response.format``, if set.
    
       #. Try looking at any explicitly set ``Content-Type`` in `response`.
    
       #. Try looking at request filename extension, derived from
          ``request.url.path``.
    
       #. Try looking at media types in request ``Accept`` header.
    
       #. Use `Response.fallback_serializer` or raise `http.MultipleChoices`,
          depending on value of ``no_http_exc`` method argument.
    
    #. Parse request using `parse_request()`.
   
       #. Update request parameters with any query string parameters.
   
       #. Register for the client acceptable character encodings by looking 
          at any ``Accept-Charset`` header.
   
       #. Update request parameters and arguments with any POST body, possibly
          by using a serializer to decode the request body.
    
    #. Resolve *controller leaf* by calling `routes`.
    
       #. Apply any route filters.
   
       #. Resolve *leaf* on the *controller tree*.
    
    #. Apply any format restrictions defined by the current *controller leaf*.
    
    #. Append ``Vary`` header to response, with the value ``negotiate, accept,
       accept-charset``.
    
    #. Call the *controller leaf* which will return a *response object*.
    
       #. Applies any "before" filters.
    
       #. Calls the *controller leaf*
    
       #. Applies any "after" filters.
    
    #. Flush the model/database session, if started or modified, committing any
       modifications.
    
    #. If a templates are used, and the current *controller leaf* is associated 
       with a template – aquire the template object for later use in 
       `encode_response()`.
    
    #. Encode the *response object* using `encode_response()`, resulting in a
       string of opaque bytes which constitutes the response body, or payload.
    
       #. If the *response object* is ``None``, either render the current template
          (if any) without any parameters or fall back to `encode_response()` 
          returning ``None``.
    
       #. If the *response object* is a string, encode it if needed and simply
          return the string, resulting in the input to `encode_response()`
          compares equally to the output.
    
       #. If a template object has been deduced from previous algorithms, 
          serialize the *response object* using that template object.
    
       #. Otherwise, if no template is used, serialize the *response object* using
          the previously deduced response serializer.
    
    #. Complete (or commit) the current HTTP transaction by sending the response
       by calling `send_response()`.
    
       #. Set ``Content-Length`` and other response headers, unless the response has
          already begun.
    
       #. Calculate *ETag* if enabled through the `etag` attribute.
    
       #. Write the response body.
    
    
    :rtype: None
    '''
    if log.level <= logging.INFO:
      timer = Timer()
      log.info('Serving %s for client %s', request.url, request.env.get('REMOTE_ADDR','?'))
    
    # Reset pre-transaction properties
    self.request.serializer = None
    self.response.format = None
    self.response.serializer = None
    self.response.charset = Response.charset
    self.destination = None
    self.template = None
    
    # Aquire response serializer.
    # We do this here already, because if response_serializer() raises and
    # exception, we do not want any action to be performed. If we would do this
    # after calling an action, chances are an important answer gets replaced by
    # an error response, like 406 Not Acceptable.
    self.response.serializer = self.response_serializer()
    if self.response.serializer.charset is not None:
      self.response.charset = self.response.serializer.charset
    
    # Parse request (and decode if needed)
    req_args, req_params = self.parse_request()
    
    # Resolve route to destination
    self.destination, req_args, req_params = \
      self.routes(self.request.url, req_args, req_params)
    
    # Adjust formats if required by destination
    self.apply_action_format_restrictions()
    
    # Call the action which might generate a response object: rsp
    try:
      rsp = self.call_action(req_args, req_params)
    except http.HTTPExc, e:
      if e.status.is_error:
        log.info('rolling back db transaction')
        model.session.rollback()
      else:
        log.info('committing db transaction before handling non-error http status')
        model.session.flush()
      raise
    except:
      log.info('rolling back db transaction')
      model.session.rollback()
      raise
    
    # Flush model session
    model.session.flush()
    
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
        uri = self.request.url.to_s(scheme=0, user=0, password=0, host=0, port=0)
      log.info('Processed %s in %.3fms', uri, timer.time()*1000.0)
  
  
  def template_for_path(self, path):
    '''Aquire template URI for `path`.
    
    :Parameters:
      path : string
        A relative path
    :rtype: template.Template
    '''
    return self.template_for_uri(self.template_uri_for_path(path))
  
  
  def template_uri_for_path(self, path):
    '''Get template URI for `path`.
    
    :Parameters:
      path : string
        A relative path
    :rtype: string
    '''
    return path + '.' + self.response.serializer.extensions[0]
  
  
  def template_for_uri(self, uri):
    '''Aquire template for `uri`.
    
    :Parameters:
      uri : string
        Path
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
  
  def error(self, typ, val, tb):
    '''Handle an error and produce an appropriate response.
    
    :Parameters:
      typ : type
        Exception type
      val : object
        Exception value
      tb : traceback
        Traceback
    :rtype: None
    '''
    try:
      status = getattr(val, 'status', http.InternalServerError)
      if not isinstance(status, http.Status):
        status = http.InternalServerError
      params = {}
      rsp = None
      
      # Log
      if status.is_error:
        log.error('%d Request failed for %r', status.code, self.request.url.path, exc_info=(typ, val, tb))
      else:
        log.warn('Request failed for %r -- %s: %s', self.request.url.path, typ.__name__, val)
      
      # Set headers
      self.response.headers = [
        'Status: %s' % status,
        'Vary: Accept, Accept-Charset'
      ]
      
      # Set params
      params['name'] = unicode(status.name)
      params['code'] = status.code
      params['server'] = u'%s at %s' % (self.request.env['SERVER_SOFTWARE'],
        self.request.env['SERVER_NAME'])
      
      # Include traceback if enabled
      if self.show_traceback:
        params['traceback'] = format_exc((typ, val, tb))
      else:
        params['traceback'] = None
      
      # HTTP exception has a bound action we want to call
      if isinstance(val, http.HTTPExc):
        status_service_rsp = val(self)
        if isinstance(status_service_rsp, StringType):
          rsp = status_service_rsp
        elif status_service_rsp:
          assert isinstance(status_service_rsp, DictType)
          params.update(status_service_rsp)
      if not params.get('description', False):
        params['description'] = unicode(val)
      
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
            self.response.charset, rsp = self.response.serializer.serialize_error(status, params, \
              self.response.charset)
        
        # MSIE body length fix
        rsp = self._pad_rsp_for_msie(status.code, rsp)
      else:
        rsp = ''
      
      # Set standard headers
      if not self.response.has_begun:
        if self.response.serializer:
          self.response.serializer.add_content_type_header(self.response, self.response.charset)
        if self.response.find_header('Content-Length:') == -1:
          self.response.headers.append('Content-Length: %d' % len(rsp))
        if self.response.find_header('Cache-Control:') == -1:
          self.response.headers.append('Cache-Control: no-cache')
      
      # Send response
      if log.level <= logging.DEBUG:
        self._log_debug_sending_rsp(rsp)
      self.response.write(rsp)
      
      return # We're done.
    
    except:
      log.error('Failed to encode error', exc_info=1)
    log.error('Request failed for %r', self.request.url.path, exc_info=(typ, val, tb))
    super(Application, self).error(typ, val, tb)
  

_is_set_up = False

def setup(application=None, appdir=None, *args, **kwargs):
  '''Helper for setting up an application.
  
  Excessive arguments and keyword arguments are passed to `mvc.Application.__init__()`.
  If `application` is already an instance, these extra arguments and keyword arguments
  have no effect.
  
  This function can only be called once. Successive calls simply returns the
  current application without making any modifications. If you want to update
  the application state, see `Application.setup()` instead, which can be called
  multiple times.
  
  **The application argument**
  
  * If `application` is not provided or ``None``, app will be aquired by calling
    `Application.current` if there is an application. Otherwise, a new
    application instance of default type is created and in which case any extra
    args and kwargs are passed to it's ``__init__``.
  
  * If `application` is a type, it has to be a subclass of `smisk.core.Application` in
    which case a new instance of that type is created and passed any extra
    args and kwargs passed to this function.
  
  **Application directory**
  
  The application directory is the physical path in which your application module
  resides in the file system. Smisk need to know this and tries to automatically
  figure it out. However, there are cases where you need to explicitly define your
  application directory. For instance, if you'r calling `main()` or `setup()` from
  a sub-module of your application.
  
  There are currently two ways of manually setting the application directory:
  
  1. If `appdir` **is** specified, the environment variable ``SMISK_APP_DIR`` will
     be set to it's value, effectively overwriting any previous value.
    
  2. If `appdir` is **not** specified the application directory path will be aquired
     by ``dirname(__main__.__file__)``.
  
  **Environment variables**
  
  SMISK_APP_DIR
    The physical location of the application.
    If not set, the value will be calculated like ``abspath(appdir)`` if the
    `appdir` argument is not None. In the case `appdir` is None, the value 
    is calculated like this: ``dirname(<__main__ module>.__file__)``.
  
  SMISK_ENVIRONMENT
    Name of the current environment. If not set, this will be set to the 
    default value returned by 'environment()'.
  
  
  :Parameters:
    application : Application
      An application type or instance.
    appdir : string
      Path to the applications base directory. Setting this will overwrite
      any previous value of environment variable ``SMISK_APP_DIR``.
  
  :returns: The application
  :rtype: `Application`
  :see: `run()`
  :see: `main()`
  '''
  global _is_set_up
  if _is_set_up:
    return app
  _is_set_up = True
  
  # Make sure SMISK_APP_DIR is set correctly
  setup_appdir(appdir)
  
  # Simpler environment() function
  os.environ['SMISK_ENVIRONMENT'] = environment()
  
  # Aquire app
  if not application:
    application = app
    if not application:
      application = Application(*args, **kwargs)
  elif type(application) is type:
    if not issubclass(application, smisk.core.Application):
      raise ValueError('application is not a subclass of smisk.core.Application')
    application = application(*args, **kwargs)
  elif not isinstance(application, smisk.core.Application):
    raise ValueError('application is not an instance of smisk.core.Application')
  
  # Load config
  application.autoload_configuration()
  
  # Setup
  application.setup()
  
  return application


def run(bind=None, application=None, forks=None, handle_errors=False):
  '''Helper for running an application.
  
  Note that because of the nature of ``libfcgi`` an application can not 
  be started, stopped and then started again. That said, you can only start 
  your application once per process. (Details: OS_ShutdownPending sets a 
  process-wide flag causing any call to accept to bail out)
  
  **Environment variables**
  
  SMISK_BIND
    If set and not empty, a call to ``smisk.core.bind`` will occur, passing
    the value to bind, effectively starting a stand-alone process.
  
  :Parameters:
    bind : string
      Bind to address (and port). Note that this overrides ``SMISK_BIND``.
    application : Application
      An application type or instance.
    forks : int
      Number of child processes to spawn.
    handle_errors : bool
      Handle any errors by wrapping calls in `handle_errors_wrapper()`
  
  :returns: Anything returned by ``application.run()``
  :rtype: object
  
  :see: `setup()`
  :see: `main()`
  '''
  # Aquire app
  if not application:
    if app:
      application = app.current
    else:
      raise ValueError('No application has been set up. Run setup() before calling run()')
  elif not isinstance(application, smisk.core.Application):
    raise ValueError('"application" attribute must be an instance of smisk.core.Application or a '\
      'subclass there of, not %s' % type(application).__name__)
  
  # Bind
  if bind is not None:
    os.environ['SMISK_BIND'] = bind
  if 'SMISK_BIND' in os.environ:
    smisk.core.bind(os.environ['SMISK_BIND'])
    log.info('Listening on %s', smisk.core.listening())
  
  # Enable auto-reloading
  if application.autoreload:
    from smisk.autoreload import Autoreloader
    ar = Autoreloader()
    ar.start()
  
  # Forks
  if isinstance(forks, int):
    application.forks = forks
  
  # Call app.run()
  if handle_errors:
    return handle_errors_wrapper(application.run)
  else:
    return application.run()


def main(application=None, appdir=None, bind=None, forks=None, handle_errors=True, cli=True, *args, **kwargs):
  '''Helper for setting up and running an application.
  
  This function handles command line options, calls `setup()` to set up the
  application, and then calls `run()`, entering the runloop.
  
  This is normally what you do in your top module ``__init__``::
  
    from smisk.mvc import main
    if __name__ == '__main__':
      main()
  
  Your module is now a runnable program which automatically configures and
  runs your application.
  
  Excessive arguments and keyword arguments are passed to `mvc.Application.__init__()`.
  If `application` is already an instance, these extra arguments and keyword arguments
  have no effect.
  
  :Parameters:
    application : Application
      An application type or instance.
    appdir : string
      Path to the applications base directory.
    bind : string
      Bind to address (and port). Note that this overrides ``SMISK_BIND``.
    forks : int
      Number of child processes to spawn.
    handle_errors : bool
      Handle any errors by wrapping calls in `handle_errors_wrapper()`
    cli : bool
      Act as a *Command Line Interface*, parsing command line arguments and
      options.
  
  :Returns: Anything returned by ``app.run()``
  :rtype: object
  
  :see:   `setup()`
  :see:   `run()`
  '''
  if cli:
    appdir, bind, forks = main_cli_filter(appdir=appdir, bind=bind, forks=forks)
  
  # Setup
  if handle_errors:
    application = handle_errors_wrapper(setup, application=application, 
      appdir=appdir, *args, **kwargs)
  else:
    application = setup(application=application, appdir=appdir, *args, **kwargs)
  
  # Run
  return run(bind=bind, application=application, forks=forks, handle_errors=handle_errors)



