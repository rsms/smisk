# encoding: utf-8
'''Model-View-Controller-based sub-framework.

Example application

.. python::
  from smisk.mvc import Controller, main
  class root(Controller):
    def __call__(self, *args, **params):
      return {'message': 'Hello World!'}
  
  main()

.. packagetree::
'''
import sys, os, logging, codecs as char_codecs
from types import DictType
import smisk, smisk.core
import http, control, model

from smisk.core import URL
from smisk.util import *
from smisk.codec import codecs

from control import Controller
from model import Entity
from template import Templates
from routing import Router
from exceptions import *
from decorators import *

log = logging.getLogger(__name__)
application = None
request = None
response = None

# MSIE error body sizes
_MSIE_ERROR_SIZES = { 400:512, 403:256, 404:512, 405:256, 406:512, 408:512,
                      409:512, 410:256, 500:512, 501:512, 505:512}

def environment():
  """Return the name of the current environment. Defaults to 'stable'.
  
  Returns the ``SMISK_ENVIRONMENT`` environment value if available,
  otherwise returns the string 'stable'.
  
  :returns: Name of the current environment.
  :rtype: string
  """
  try:
    return os.environ['SMISK_ENVIRONMENT']
  except KeyError:
    return 'stable'


class Request(smisk.core.Request):
  codec = None
  '''Codec used for decoding request payload.
  
  Any initial value has no effect.
  Available during a HTTP transaction.
  
  :type: smisk.codec.BaseCodec
  '''
  
  path = None
  '''Requested URL path without any filename extension.
  
  Any initial value has no effect.
  Available during a HTTP transaction.
  
  :type: string
  '''


class Response(smisk.core.Response):
  format = None
  '''Any value which is a valid key of the codecs.extensions dict.
  
  Any initial value has no effect (replaced during runtime).
  
  :type: string
  '''
  
  codec = None
  '''Codec to use for encoding the response.
  
  The value of ``Response.codec`` (class property value) serves as
  the application default codec, used in cases where we need to encode 
  the response, but the client is not specific about which codec to use.
  
  If None, strict `TCN <http://www.ietf.org/rfc/rfc2295.txt>`__ applies.
  
  :see: `fallback_codec`
  :type: smisk.codec.BaseCodec
  '''
  
  fallback_codec = None
  '''Last-resort codec, used for error responses and etc.
  
  If None when `Application.application_will_start` is called, this will
  be set to a HTML-codec, and if none is available, simply the first
  registered codec will be used.
  
  The class property is the only one used, the instance property has no 
  meaning and no effect, thus if you want to modify this during runtime,
  you should do this ``Response.fallback_codec = my_codec`` instead of
  this ``app.response.fallback_codec = my_codec``.
  
  :type: smisk.codec.BaseCodec
  '''
  
  charset = 'utf-8'
  '''Character encoding used to encode the response body.
  
  The value of ``Response.charset`` (class property value) serves as
  the application default charset.
  
  :type: string
  '''
  


class Application(smisk.core.Application):
  '''MVC application
  '''
  
  templates = None
  ''':type: Templates
  '''
  
  autoreload = False
  ''':type: bool
  '''
  
  strict_tcn = True
  '''Controls where there or not this application is strict about
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
  string rep when:
  
  .. python::
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
  
  codec = None
  '''
  Used during runtime.
  Here because we want to use it in error()
  
  :type: codec
  '''
  
  destination = None
  '''
  Used during runtime.
  Available in actions, codecs and templates.
  
  :type: smisk.mvc.routing.Destination
  '''
  
  template = None
  '''
  Used during runtime.
  
  :type: mako.template.Template
  '''
  
  def __init__(self,
               autoreload=False,
               etag=None, 
               router=None,
               templates=None,
               show_traceback=False,
               log_level=logging.WARN,
               log_format='%(levelname)-8s %(name)-20s %(message)s',
               *args, **kwargs):
    self.request_class = Request
    self.response_class = Response
    super(Application, self).__init__(*args, **kwargs)
    
    # Basic config
    logging.basicConfig(
      level=log_level,
      format = log_format,
      datefmt = '%d %b %H:%M:%S'
    )
    
    self.etag = etag
    self.autoreload = autoreload
    self.show_traceback = show_traceback
    
    if router is None:
      self.routes = Router()
    else:
      self.routes = router
    
    if templates is None:
      self.templates = Templates(app=self)
    else:
      self.templates = templates
    
    self._setup = False
  
  
  def autoload_configuration(self, config_mod_name='config'):
    import imp
    path = os.path.join(os.environ['SMISK_APP_DIR'], config_mod_name)
    locs = {'app': self}
    if not os.path.exists(path):
      log.info('No configuration found -- no %s module in %s.', config_mod_name, path)
      return
    if os.path.isdir(path):
      execfile(os.path.join(path, '__init__.py'), globals(), locs)
      log.info('Loaded configuration from module %r', config_mod_name)
      path = os.path.join(path, '%s.py' % environment())
      if os.path.exists(path):
        execfile(path, globals(), locs)
        log.info('Loaded configuration (for %r environment) from module %s.%s',
                 environment(), config_mod_name, environment())
      else:
        log.debug('No configuration found for active environment (%s) -- '\
                  'no %s.%s module in application.', environment(), 
                  config_mod_name, environment())
  
  
  def setup(self):
    '''Setup application.
    
    Can be called multiple times.
    Automatically called by `application_will_start()`.
    
    :rtype: None
    '''
    # Setup ETag
    if self.etag is not None and isinstance(self.etag, basestring):
      import hashlib
      self.etag = getattr(hashlib, self.etag)
    
    # Check templates config
    if self.templates:
      if not self.templates.directories:
        self.templates.directories = [os.path.join(os.environ['SMISK_APP_DIR'], 'templates')]
      if self.templates.autoreload is None:
        self.templates.autoreload = self.autoreload
    
    # Set fallback codec
    if Response.fallback_codec is None:
      try:
        Response.fallback_codec = codecs.extensions['html']
      except KeyError:
        Response.fallback_codec = codecs.first_in
    
    # Setup any models
    model.setup_all()
    
    # Info about codecs
    if not self._setup and log.level <= logging.DEBUG:
      log.debug('installed codecs: %s', ', '.join(unique_sorted_modules_of_items(codecs)) )
      log.debug('acceptable media types: %s', ', '.join(codecs.media_types.keys()))
      log.debug('available filename extensions: %s', ', '.join(codecs.extensions.keys()))
      log.debug('Template directories: %s', ', '.join(self.templates.directories))
    
    self._setup = True
  
  
  def application_will_start(self):
    self.setup()
    
    # Initialize modules which need access to app, request and response
    modules = find_modules_for_classtree(control.Controller)
    modules.extend(find_modules_for_classtree(Entity))
    for m in modules:
      log.debug('Initializing app module %s', m.__name__)
      m.app = self
      m.request = self.request
      m.response = self.response
    
    # Set references in this module to live instances
    global application, request, response
    application = self
    request = self.request
    response = self.response
    
    # When we return, accept() in smisk.core is called
    log.info('Accepting connections')
  
  
  def application_did_stop(self):
    model.cleanup_all()
    smisk.core.unbind()
  
  
  def response_codec(self, no_http_exc=False):
    '''
    Return the most appropriate codec for handling response encoding.
    
    :param no_http_exc: If true, HTTP statuses are never rised when no acceptable 
                        codec is found. Instead a fallback codec will be returned:
                        First we try to return a codec for format html, if that
                        fails we return the first registered codec. If that also
                        fails there is nothing more left to do but return None.
                        Primarily used by `error()`.
    :type  no_http_exc: bool
    :return: The most appropriate codec
    :rtype:  codec
    '''
    # Overridden by explicit response.format?
    if self.response.format is not None:
      # Should fail if not exists
      return codecs.extensions[self.response.format]
    
    # Overridden internally by explicit Content-Type header?
    p = self.response.find_header('Content-Type:')
    if p != -1:
      content_type = self.response.headers[p][13:].strip("\t ").lower()
      p = content_type.find(';')
      if p != -1:
        content_type = content_type[:p].rstrip("\t ")
      try:
        return codecs.media_types[content_type]
      except KeyError:
        if no_http_exc:
          return Response.fallback_codec
        else:
          raise http.InternalServerError('Content-Type response header is set to type %r '\
            'which does not have any valid codec associated with it.' % content_type)
    
    # Try filename extension
    if self.request.url.path.rfind('.') != -1:
      filename = os.path.basename(self.request.url.path)
      p = filename.rfind('.')
      if p != -1:
        self.request.path = strip_filename_extension(self.request.url.path)
        self.response.format = filename[p+1:].lower()
        if log.level <= logging.DEBUG:
          log.debug('Client asked for format %r', self.response.format)
        try:
          return codecs.extensions[self.response.format]
        except KeyError:
          if no_http_exc:
            return Response.fallback_codec
          else:
            raise http.NotFound('Resource not available as %r' % self.response.format)
    
    # Try media type
    accept_types = self.request.env.get('HTTP_ACCEPT', None)
    if accept_types is not None and len(accept_types):
      if log.level <= logging.DEBUG:
        log.debug('Client accepts: %r', accept_types)
      
      # Parse the qvalue header
      tqs, highqs, partials, accept_any = parse_qvalue_header(accept_types, '*/*', '/*')
      
      # If the default codec exists in the highest quality accept types, return it
      if Response.codec is not None:
        for t in Response.codec.media_types:
          if t in highqs:
            return Response.codec
      
      # Find a codec matching any accept type, ordered by qvalue
      available_types = codecs.media_types.keys()
      for tq in tqs:
        t = tq[0]
        if t in available_types:
          return codecs.media_types[t]
      
      # Accepts */* which is far more common than accepting partials, so we test this here
      # and simply return Response.codec if the client accepts anything.
      if accept_any:
        if Response.codec is not None:
          return Response.codec
        else:
          return Response.fallback_codec
      
      # If the default codec matches any partial, return it (the likeliness of 
      # this happening is so small we wait until now)
      if Response.codec is not None:
        for t in Response.codec.media_types:
          if t[:t.find('/', 0)] in partials:
            return Response.codec
      
      # Test the rest of the partials
      for t, codec in codecs.media_types.items():
        if t[:t.find('/', 0)] in partials:
          return codec
      
      # If an Accept header field is present, and if the server cannot send a response which 
      # is acceptable according to the combined Accept field value, then the server SHOULD 
      # send a 406 (not acceptable) response. [RFC 2616]
      log.info('Client demanded content type(s) we can not respond in. "Accept: %s"', accept_types)
      if self.strict_tcn:
        raise http.NotAcceptable()
    
    # The client did not ask for any type in particular
    
    # Strict TCN
    if Response.codec is None:
      if no_http_exc:
        return Response.fallback_codec
      else:
        raise http.MultipleChoices(self.request.url)
      
    # Return the default codec
    return Response.codec
  
  
  def parse_request(self):
    '''
    Parses the request, involving appropriate codec if needed.
    
    :returns: (list arguments, dict parameters)
    :rtype:   tuple
    '''
    args = []
    
    # Set params to the query string
    params = self.request.get
    for k,v in params.iteritems():
      params[k.decode('utf-8')] = v.decode('utf-8')
    
    # If request.path has not yet been deduced, simply set it to request.url.path
    if self.request.path is None:
      self.request.path = self.request.url.path
    
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
          self.request.codec = codecs.media_types[content_type]
          log.debug('decoding POST data using %s', self.request.codec)
          content_length = int(self.request.env.get('CONTENT_LENGTH', -1))
          (eargs, eparams) = self.request.codec.decode(self.request.input, content_length)
          if eargs is not None:
            args.extend(eargs)
          if eparams is not None:
            params.update(eparams)
        except KeyError:
          log.error('Unable to parse request -- no codec able to decode %r', content_type)
          raise http.UnsupportedMediaType()
    
    return (args, params)
  
  
  def apply_action_format_restrictions(self):
    '''Applies any format restrictions set by the current action.
    
    :rtype: None
    '''
    try:
      action_formats = self.destination.action.formats
      for ext in self.response.codec.extensions:
        if ext not in action_formats:
          self.response.codec = None
          break
      if self.response.codec is None:
        log.warn('client requested a response type which is not available for the current action')
        if self.response.format is not None:
          raise http.NotFound('Resource not available as %r' % self.response.format)
        elif self.strict_tcn or len(action_formats) == 0:
          raise http.NotAcceptable()
        else:
          try:
            self.response.codec = codecs.extensions[action_formats[0]]
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
    if self.response.codec and (\
          not self.response.format \
        or \
          (self.destination.uri and self.destination.uri != self.request.path)\
        ):
      self.response.headers.append('Content-Location: %s.%s' % \
        (self.destination.uri, self.response.codec.extension))
    
    # Call action
    if log.level <= logging.DEBUG:
      log.debug('Calling destination %r', self.destination)
    return self.destination(*args, **params)
  
  
  def encode_response(self, rsp):
    # No data to encode
    if rsp is None:
      if self.template:
        return self.template.render_unicode().encode(self.response.charset)
      return None
    
    # If rsp is already a string, we do not process it further
    if isinstance(rsp, basestring):
      if not isinstance(rsp, str):
        if isinstance(rsp, unicode):
          rsp = rsp.encode(self.response.charset)
        else:
          rsp = str(rsp)
        return rsp
    
    # Make sure rsp is a dict
    if not isinstance(rsp, dict):
      raise ValueError('Actions must return a dict, a string or None, not %s' % type(rsp).__name__)
    
    # Use template as codec, if available
    if self.template:
      return self.template.render_unicode(**rsp).encode(self.response.charset)
    
    # If we do not have a template, we use a data codec
    self.response.charset, rsp = self.response.codec.encode(rsp, self.response.charset)
    return rsp
  
  
  def send_response(self, rsp):
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
      self.response.codec.add_content_type_header(self.response, self.response.charset)
      # Add ETag
      if self.etag is not None and len(rsp) > 0 and self.response.find_header('ETag:') == -1:
        h = self.etag(''.join(self.response.headers))
        h.update(rsp)
        self.response.headers.append('ETag: "%s"' % h.hexdigest())
    
    # Debug print
    if log.level <= logging.DEBUG:
      self._log_debug_sending_rsp(rsp)
    
    # Send body
    assert(isinstance(rsp, basestring))
    self.response.write(rsp)
  
  
  def service(self):
    if log.level <= logging.INFO:
      timer = Timer()
      log.info('Serving %s for client %s', request.url, request.env.get('REMOTE_ADDR','?'))
    
    # Reset pre-transaction properties
    self.request.codec = None
    self.request.path = None
    self.response.format = None
    self.response.codec = None
    self.response.charset = Response.charset
    self.destination = None
    self.template = None
    
    # Aquire response codec.
    # We do this here already, because if response_codec() raises and
    # exception, we do not want any action to be performed. If we would do this
    # after calling an action, chances are an important answer gets replaced by
    # an error response, like 406 Not Acceptable.
    self.response.codec = self.response_codec()
    if self.response.codec.charset is not None:
      self.response.charset = self.response.codec.charset
    
    # Parse request (and decode if needed)
    req_args, req_params = self.parse_request()
    
    # Resolve route to destination
    self.destination, req_args, req_params = \
      self.routes(self.request.url, req_args, req_params)
    
    # Adjust formats if required by destination
    self.apply_action_format_restrictions()
    
    # Always add the vary header, because we do (T)CN
    self.response.headers.append('Vary: negotiate, accept, accept-charset')
    
    # Call the action which might generate a response object: rsp
    rsp = self.call_action(req_args, req_params)
    
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
        uri = '%s.%s' % (self.destination.uri, self.response.codec.extension)
      else:
        uri = self.request.url.to_s(scheme=0, user=0, password=0, host=0, port=0)
      log.info('Processed %s in %.3fms', uri, timer.time()*1000.0)
  
  
  def template_for_path(self, path):
    return self.template_for_uri(self.template_uri_for_path(path))
  
  
  def template_uri_for_path(self, path):
    return path + '.' + self.response.codec.extension
  
  
  def template_for_uri(self, uri):
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
    try:
      status = getattr(val, 'status', http.InternalServerError)
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
        'Vary: negotiate, accept, accept-charset'
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
        if isinstance(status_service_rsp, basestring):
          rsp = status_service_rsp
        elif status_service_rsp:
          assert(type(status_service_rsp) is DictType)
          params.update(status_service_rsp)
      if not params.get('description', False):
        params['description'] = unicode(val)
      
      # Ony perform the following block if status type has a body and if
      # status_service_rsp did not contain a complete response body.
      if status.has_body:
        if rsp is None:
          # Try to use a codec
          if self.response.codec is None:
            # In this case an error occured very early.
            self.response.codec = Response.fallback_codec
            log.info('Responding using fallback codec %s' % self.response.codec)
          
          # Set format if a codec was found
          format = self.response.codec.extension
          
          # Try to use a template...
          if status.uses_template:
            rsp = self.templates.render_error(status, params, format)
          
          # ...or a codec
          if rsp is None:
            self.response.charset, rsp = self.response.codec.encode_error(status, params, \
              self.response.charset)
        
        # MSIE body length fix
        rsp = self._pad_rsp_for_msie(status.code, rsp)
      else:
        rsp = ''
      
      # Set standard headers
      if not self.response.has_begun:
        if self.response.codec:
          self.response.codec.add_content_type_header(self.response, self.response.charset)
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

def setup(app=None, appdir=None, *args, **kwargs):
  '''Helper for running an application.
  
  If `app` is not provided or None, app will be aquired by calling
  ``Application.current`` if there is an application. Otherwise, a new
  application instance of default type is created and in which case any extra
  args and kwargs are passed to it's __init__.
  
  If `app` is a type, it has to be a subclass of `smisk.core.Application` in
  which case a new instance of that type is created and passed any extra
  args and kwargs passed to this function.
  
  If `appdir` is specified and SMISK_APP_DIR is present in os.environ, the
  value of appdir will be replaced by the value of SMISK_APP_DIR. It is
  constructed like this to allow for overloading using the env.
  
  If `appdir` is not specified the application directory path will be aquired
  by ``dirname(__main__.__file__)`` and if that's not possible, the current
  working directory is used.
  
  Environment variables
  ---------------------
  
  SMISK_APP_DIR
    The physical location of the application.
    If not set, the value will be calculated like ``abspath(appdir)`` if the
    `appdir` argument is not None. In the case `appdir` is None, the value 
    is calculated like this: ``dirname(<__main__ module>.__file__)``.
  
  SMISK_ENVIRONMENT
    Name of the current environment. If not set, this will be set to the 
    default value returned by 'environment()'.
  
  :param app:     An application type or instance.
  :type  app:     Application
  :param appdir:  Path to the applications base directory.
  :type  appdir:  string
  :rtype: None
  :see: `run()`
  :see: `main()`
  '''
  global _is_set_up
  if _is_set_up:
    return Application.current
  _is_set_up = True
  
  # Make sure SMISK_APP_DIR is set correctly
  if 'SMISK_APP_DIR' not in os.environ:
    if appdir is None:
      try:
        appdir = os.path.dirname(sys.modules['__main__'].__file__)
      except:
        raise EnvironmentError('unable to calculate SMISK_APP_DIR because: %s' % sys.exc_info())
    os.environ['SMISK_APP_DIR'] = os.path.abspath(appdir)
  
  # Simpler environment() function
  global environment
  os.environ['SMISK_ENVIRONMENT'] = environment()
  def _environment():
    return os.environ['SMISK_ENVIRONMENT']
  environment = _environment
  
  # Aquire app
  if app is None:
    app = Application.current
    if app is None:
      app = Application(*args, **kwargs)
  elif type(app) is type:
    if not issubclass(app, smisk.core.Application):
      raise ValueError('app is not a subclass of smisk.core.Application')
    app = app(*args, **kwargs)
  elif not isinstance(app, smisk.core.Application):
    raise ValueError('app is not an instance of smisk.core.Application')
  
  # Load config
  app.autoload_configuration()
  
  # Setup
  app.setup()
  
  return app


def run(bind=None, app=None):
  '''Helper for running an application.
  
  Note that because of the nature of ``libfcgi`` an application can not be started, stopped and then started again. That said, you can only start your application once per process. (Details: OS_ShutdownPending sets a process-wide flag causing any call to *accept to bail out)
  
  Environment variables
  ---------------------
  
  SMISK_BIND
    If set and not empty, a call to ``smisk.core.bind`` will occur, passing
    the value to bind.
  
  :param  bind:  Bind to address (and port). Note that this overrides SMISK_BIND.
  :type   bind:  string
  :param  app:   Uses Application.current is not set or None.
  :type   app:   Application
  :rtype: None
  :see: `setup()`
  :see: `main()`
  '''
  # Aquire app
  if app is None:
    app = Application.current
  if app is None:
    raise ValueError('No application has been set up. Run setup() before calling run()')
  
  # Bind
  if bind is not None:
    os.environ['SMISK_BIND'] = bind
  if 'SMISK_BIND' in os.environ:
    smisk.bind(os.environ['SMISK_BIND'])
    log.info('Listening on %s', smisk.listening())
  
  # Enable auto-reloading
  if app.autoreload:
    from smisk.autoreload import Autoreloader
    ar = Autoreloader()
    ar.start()
  
  # Call app.run()
  return wrap_call(app.run)


def main(app=None, bind=None, *args, **kwargs):
  '''Helper for setting up and running an application.
  
  First calls `setup()` to set up the application, then calls `run()`.
  
  :param app:     An application type or instance.
  :type  app:     Application
  :rtype: None'''
  app = wrap_call(setup, app=app, *args, **kwargs)
  run(bind=bind, app=app)


def wrap_call(fnc, error_cb=sys.exit, abort_cb=None, *args, **kwargs):
  '''Call `fnc` catching any errors and writing information to ``error.log``.
  
  ``error.log`` will be written to, or appended to if it aldready exists,
  ``ENV["SMISK_LOG_DIR"]/error.log``. If ``SMISK_LOG_DIR`` is not set,
  the file will be written to ``ENV["SMISK_APP_DIR"]/error.log``.
  
  * ``KeyboardInterrupt`` is discarded/passed, causing a call to `abort_cb`,
    if set, without any arguments.
  
  * ``SystemExit`` is passed on to Python and in normal cases causes a program
    termination, thus this function will not return.
  
  * Any other exception causes ``error.log`` to be written to and finally
    a call to `error_cb` with a single argument; exit status code.
  
  :param  error_cb:   Called after an exception was caught and info 
                               has been written to ``error.log``. Receives a
                               single argument: Status code as an integer.
                               Defaults to ``sys.exit`` causing normal program
                               termination. The returned value of this callable
                               will be returned by `wrap_call` itself.
  :type   error_cb:   callable
  :param  abort_cb:   Like `error_cb` but instead called when
                      ``KeyboardInterrupt`` was raised.
  :type   abort_cb:   callable
  :rtype: object
  '''
  try:
    # Run the wrapped callable
    return fnc(*args, **kwargs)
  except KeyboardInterrupt:
    if abort_cb:
      return abort_cb()
  except SystemExit:
    raise
  except:
    # Log error
    try:
      log.critical('exception:', exc_info=True)
    except:
      pass
    # Write to error.log
    try:
      log_dir = os.environ.get('SMISK_LOG_DIR' ,os.environ['SMISK_APP_DIR'])
      f = open(os.path.join(log_dir, 'error.log'), 'a')
      try:
        from traceback import print_exc
        from datetime import datetime
        f.write(datetime.now().isoformat())
        f.write(" [")
        f.write(os.getpid())
        f.write("] ")
        print_exc(1000, f)
      finally:
        f.close()
    except:
      pass
    # Call error callback
    if error_cb:
      return error_cb(1)
