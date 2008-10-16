# encoding: utf-8
import sys, os, logging, codecs as char_codecs
from types import DictType
import smisk, smisk.core
import http, control

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


class Response(smisk.core.Response):
  format = None
  '''
  Any value which is a valid key of the codecs.extensions dict.
  
  :type: string
  '''
  
  status = http.OK
  ''':type: smisk.mvc.http.Status'''


class Application(smisk.core.Application):
  '''MVC application'''
  
  default_response_charset = 'utf-8'
  '''
  Default response character encoding.
  
  :type: string
  '''
  
  default_format = 'html'
  ''':type: string'''
  
  templates = None
  ''':type: Templates'''
  
  autoreload = False
  ''':type: bool'''
  
  strict_content_negotiation = True
  '''
  Controls where there or not this application is strict about content
  negotiation.
  
  For example, if this is True and a client accepts only character sets 
  none of which can encode, a 206 Not Acceptable response is sent.
  
  This affects ``Accept*`` request headers which demands can not be met.
  
  As HTTP 1.1 (RFC 2616) allows fallback to defaults (though not 
  recommended) we provide the option of turning of the 206 response.
  Setting this to false will respond using a best-guess of what value
  to use in place of the demanded value which could no be met.
  
  :type: bool'''
  
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
  ''':type: string'''
  
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
               *args, **kwargs):
    self.response_class = Response
    super(Application, self).__init__(*args, **kwargs)
    
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
  
  
  def autoload_configuration(self, config_mod_name='config'):
    import imp
    path = os.path.join(os.environ['SMISK_APP_DIR'], config_mod_name)
    locs = {'app': self}
    if not os.path.exists(path):
      log.info('No configuration found -- no %s module in application.', config_mod_name)
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
    return
    
    locs = {'app': self}
    try:
      __import__(config_mod_name, globals(), locs)
      log.info('Loaded application-wide configuration from module %r', config_mod_name)
      environment_mod_name = '%s.%s' % (config_mod_name, environment())
      try:
        __import__(environment_mod_name, globals(), locs)
        log.info('Loaded application configuration for %s environment from module %r', 
                 environment(), environment_mod_name)
      except ImportError:
        log.debug('No configuration found for active environment (%r). '\
                 'No module %r in your application.', environment(), environment_mod_name)
    except ImportError:
      log.info('No configuration found. No module %r in your application.', config_mod_name)
  
  
  def application_will_start(self):
    # Make sure the router has a reference to to app
    self.routes.app = self
    
    # Basic config
    logging.basicConfig(
      level=logging.WARN,
      format = '%(levelname)-8s %(name)-20s %(message)s',
      datefmt = '%d %b %H:%M:%S'
    )
    
    # Setup ETag
    if self.etag is not None and isinstance(self.etag, basestring):
      import hashlib
      self.etag = getattr(hashlib, self.etag)
    
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
    
    # Check so the default media type really has an available codec
    codec_exts = codecs.extensions.keys()
    if not self.default_format in codec_exts:
      if len(codecs.extensions) == 0:
        log.warn('No codecs available!')
      else:
        self.default_format = codecs.extensions.keys()[0]
        log.warn('app.default_format is not available from the current set of codecs'\
                 ' -- setting to first registered codec: %s', self.default_format)
    
    # Check templates config
    if self.templates:
      if not self.templates.directories:
        self.templates.directories = [os.path.join(os.environ['SMISK_APP_DIR'], 'templates')]
      if self.templates.autoreload is None:
        self.templates.autoreload = self.autoreload
    
    # Info about codecs
    if log.level <= logging.DEBUG:
      log.debug('codecs: %s', ', '.join(unique_sorted_modules_of_items(codecs.values())) )
      log.debug('codec media types: %s', ', '.join(codecs.media_types.keys()))
      log.debug('codec formats: %s', ', '.join(codecs.extensions.keys()))
      log.debug('Template directories: %s', ', '.join(self.templates.directories))
    
    # When we return, accept() in smisk.core is called
    log.info('Accepting connections')
  
  
  def default_codec(self):
    """Return the default codec.
    
    If even the default format can not be used, the first registered
    codec is returned.
    """
    try:
      return codecs.extensions[self.default_format]
    except KeyError:
      return codecs.first_in
  
  
  def response_codec(self):
    '''
    Return the most appropriate codec for handling response encoding.
    
    :return: The most appropriate codec
    :rtype:  codec
    '''
    # Overridden by explicit response.format?
    if self.response.format is not None:
      # Should fail if not exists
      return codecs.extensions[self.response.format]
    
    # Overridden by explicit Content-Type header?
    p = self.response.find_header('Content-Type:')
    if p != -1:
      content_type = self.response.headers[p][13:].strip("\t ").lower()
      p = content_type.find(';')
      if p != -1:
        content_type = content_type[:p].rstrip("\t ")
      if content_type in codecs.media_types:
        return codecs.media_types[content_type]
    
    # Try filename extension
    if self.request.url.path.rfind('.') != -1:
      filename = os.path.basename(self.request.url.path)
      p = filename.rfind('.')
      if p != -1:
        ext = filename[p+1:].lower()
        if log.level <= logging.DEBUG:
          log.debug('Client asked for format %r', ext)
        try:
          return codecs.extensions[ext]
        except KeyError:
          raise http.NotFound()
    
    # Try media type
    default_codec = None
    accept_types = self.request.env.get('HTTP_ACCEPT', None)
    if accept_types is not None and len(accept_types):
      if log.level <= logging.DEBUG:
        log.debug('Client accepts: %r', accept_types)
      
      # Parse the qvalue header
      tqs, highqs, partials, accept_any = parse_qvalue_header(accept_types, '*/*', '/*')
      
      # If the default codec exists in the highest quality accept types, return it
      default_codec = self.default_codec()
      for t in default_codec.media_types:
        if t in highqs:
          return default_codec
      
      # Find a codec matching any accept type, ordered by qvalue
      available_types = codecs.media_types.keys()
      for tq in tqs:
        t = tq[0]
        if t in available_types:
          return codecs.media_types[t]
      
      # Accepts */* which is far more common than accepting partials, so we test this here
      # and simply return default_codec if the client accepts anything.
      if accept_any:
        return default_codec
      
      # If the default codec matches any partial, return it (the likeliness of 
      # this happening is so small we wait until now)
      for t in default_codec.media_types:
        if t[:t.find('/', 0)] in partials:
          return default_codec
      
      # Test the rest of the partials
      for t, codec in codecs.media_types.items():
        if t[:t.find('/', 0)] in partials:
          return codec
      
      # If an Accept header field is present, and if the server cannot send a response which 
      # is acceptable according to the combined Accept field value, then the server SHOULD 
      # send a 406 (not acceptable) response. [RFC 2616]
      log.info('Client demanded content type(s) we can not respond in. "Accept: %s"', accept_types)
      if self.strict_content_negotiation:
        raise http.NotAcceptable()
    
    # Return the default codec if the client did not specify any acceptable types
    return self.default_codec()
  
  
  def parse_request(self):
    '''
    Parses the request, involving appropriate codec if needed.
    
    :returns: (list arguments, dict parameters)
    :rtype:   tuple
    '''
    args = []
    
    # Set params to the query string
    params = self.request.get
    
    # Look at Accept-Charset header and set self.response_charset accordingly
    accept_charset = self.request.env.get('HTTP_ACCEPT_CHARSET', False)
    if accept_charset:
      cqs, highqs, partials, accept_any = parse_qvalue_header(accept_charset.lower(), '*', None)
      # If the charset we have already set is not in highq, use the first usable encoding
      if self.response_charset not in highqs:
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
          self.response_charset = alt_cs
        else:
          # If an Accept-Charset header is present, and if the server cannot send a response 
          # which is acceptable according to the Accept-Charset header, then the server 
          # SHOULD send an error response with the 406 (not acceptable) status code, though 
          # the sending of an unacceptable response is also allowed. [RFC 2616]
          log.info('Client demanded charset(s) we can not respond using. "Accept-Charset: %s"', accept_charset)
          if self.strict_content_negotiation:
            raise http.NotAcceptable()
        
        if log.level <= logging.DEBUG:
          log.debug('Using alternate response character encoding: %r (requested by client)', self.response_charset)
    
    # Parse body if POST request
    if self.request.env['REQUEST_METHOD'] == 'POST':
      content_type = self.request.env.get('CONTENT_TYPE', '').lower()
      if content_type == 'application/x-www-form-urlencoded' or len(content_type) == 0:
        # Standard urlencoded content
        params.update(self.request.post)
      else:
        # Different kind of content
        codec = codecs.media_types.get(content_type, None)
        
        # Parse content
        if codec is not None:
          content_length = int(self.request.env.get('CONTENT_LENGTH', -1))
          (eargs, eparams) = codec.decode(self.request.input, content_length)
          if eargs is not None:
            args.extend(eargs)
          if eparams is not None:
            params.update(eparams)
        else:
          log.error('No codec found for request type %r -- unable to parse request', content_type)
          raise http.HTTPExc(http.UnsupportedMediaType)
    
    return (args, params)
  
  
  def call_action(self, args, params):
    '''
    Resolves and calls the appropriate action, passing args and params to it.
    
    :returns: Response structure or None
    :rtype:   dict
    '''
    # Find destination or return None
    self.destination, args, params = self.routes(self.request.url, args, params)
    
    # Call action
    if log.level <= logging.DEBUG:
      log.debug('Calling destination %r', self.destination)
    return self.destination(*args, **params)
  
  
  def encode_response(self, rsp):
    # No input at all
    if rsp is None:
      if self.template:
        return self.template.render_unicode().encode(self.response_charset)
      return None
    
    # If rsp is already a string, we do not process it further
    if isinstance(rsp, basestring):
      if not isinstance(rsp, str):
        if isinstance(rsp, unicode):
          rsp = rsp.encode(self.response_charset)
        else:
          rsp = str(rsp)
        return rsp
    
    # Make sure rsp is a dict
    if not isinstance(rsp, dict):
      raise Exception('actions must return a dict, string or None -- not %s', type(rsp))
    
    # Use template as codec, if available
    if self.template:
      return self.template.render_unicode(**rsp).encode(self.response_charset)
    
    # If we do not have a template, we use a data codec
    self.response_charset, rsp = self.codec.encode(rsp, self.response_charset)
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
      # Set status
      if self.response.status is not None \
        and self.response.status is not http.OK \
        and self.response.find_header('Status:') == -1:
        self.response.headers.append('Status: ' + str(self.response.status)),
      # Add Content-Length header
      if self.response.find_header('Content-Length:') == -1:
        self.response.headers.append('Content-Length: %d' % len(rsp))
      # Add Content-Type header
      self.codec.add_content_type_header(self.response, self.response_charset)
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
    self.response.format = None
    self.response.status = http.OK
    self.destination = None
    self.template = None
    self.response_charset = self.default_response_charset
    
    # Aquire response codec.
    # We do this here already, because if response_codec() raises and
    # exception, we do not want any action to be performed. If we would do this
    # after calling an action, chances are an important answer gets replaced by
    # an error response, like 406 Not Acceptable.
    self.codec = self.response_codec()
    if self.codec.charset is not None:
      self.response_charset = self.codec.charset
    
    # Parse request (and decode if needed)
    req_args, req_params = self.parse_request()
    
    # Call the action which might generate a response object: rsp
    rsp = self.call_action(req_args, req_params)
    
    # Aquire template, if any
    if self.template is None and self.templates is not None:
      template_path = control.template_for(self.destination.action)
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
        uri = '/%s.%s' % ('/'.join(self.destination.path), self.codec.extension)
      else:
        uri = self.request.url.to_s(scheme=0, user=0, password=0, host=0, port=0)
      log.info('Processed %s in %.3fms', uri, timer.time()*1000.0)
  
  
  def template_for_path(self, path):
    return self.template_for_uri(self.template_uri_for_path(path))
  
  
  def template_uri_for_path(self, path):
    return path + '.' + self.codec.extension
  
  
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
  
  def error(self, typ, val, tb):
    try:
      status = getattr(val, 'status', http.InternalServerError)
      params = {}
      format = self.default_format
      
      # Set headers
      self.response.headers = ['Status: %s' % status]
      
      # Log
      if status.is_error:
        log.error('%d Request failed for %r', status.code, self.request.url.path, exc_info=(typ, val, tb))
      else:
        log.warn('Request failed for %r -- %s: %s', self.request.url.path, typ.__name__, val)
      
      # Ony perform the following block if status type has a body
      if status.has_body:
        
        # Try to use a codec
        if self.codec is None:
          try:
            self.codec = self.response_codec()
          except:
            self.codec = self.default_codec()
        
        # Set format if a codec was found
        format = self.codec.extension
        
        # HTTP exception has a bound action we want to call
        if isinstance(val, http.HTTPExc):
          params = val(self)
          assert(type(params) is DictType)
        
        # Include basic info
        params['name'] = str(status.name)
        params['code'] = status.code,
        if 'description' not in params:
          params['description'] = str(val)
        else:
          params['description'] = str(params['description'])
        params['server'] = '%s at %s' % (self.request.env['SERVER_SOFTWARE'],
          self.request.env['SERVER_NAME'])
        
        # Include traceback if enabled
        if self.show_traceback:
          params['traceback'] = format_exc((typ, val, tb))
        else:
          params['traceback'] = None
        
        # Try to use a template...
        rsp = self.templates.render_error(status, params, format)
        # ...or a codec
        if rsp is None:
          self.response_charset, rsp = self.codec.encode_error(status, params, self.response_charset)
        
        # Get rid of MSIE "friendly" error messages
        if self.request.env.get('HTTP_USER_AGENT','').find('MSIE') != -1:
          # See: http://support.microsoft.com/kb/q218155/
          ielen = _MSIE_ERROR_SIZES.get(status.code, 0)
          if ielen:
            ielen += 1
            blen = len(rsp)
            if blen < ielen:
              log.debug('Adding additional body content for MSIE')
              rsp = rsp + (' ' * (ielen-blen))
      else:
        rsp = ''
      
      # Send response
      if rsp is not None:
        # Set headers
        if not self.response.has_begun:
          if status.has_body and self.response.find_header('Content-Length:') == -1:
            self.response.headers.append('Content-Length: %d' % len(rsp))
          if status.is_error and self.response.find_header('Cache-Control:') == -1:
            self.response.headers.append('Cache-Control: no-cache')
          if status.has_body:
            self.codec.add_content_type_header(self.response, self.response_charset)
          else:
            rsp = None
        
        # Debug print
        if log.level <= logging.DEBUG:
          self._log_debug_sending_rsp(rsp)
        
        # Write body (and send headers if not yet sent)
        if rsp:
          self.response.write(rsp)
        
        # We're done.
        return
      
      # No rsp or error, so let smisk.core.Application.error() handle the response
    except:
      log.error('Failed to encode error', exc_info=1)
    log.error('Request failed for %r', self.request.url.path, exc_info=(typ, val, tb))
    super(Application, self).error(typ, val, tb)
  


def main(app=None, appdir=None, *args, **kwargs):
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
  
  :param app:     An application type or instance.
  :type  app:     Application
  :param appdir:  Path to the applications base directory.
  :type  appdir:  string
  :rtype: None'''
  try:
    # Make sure SMISK_APP_DIR is set correctly
    if 'SMISK_APP_DIR' not in os.environ:
      if appdir is None:
        try:
          appdir = os.path.abspath(os.path.dirname(sys.modules['__main__'].__file__))
        except:
          appdir = os.path.abspath('.')
      os.environ['SMISK_APP_DIR'] = appdir
    
    # Simpler environment() function
    global environment
    os.environ['SMISK_ENVIRONMENT'] = environment()
    def unsafe_environment():
      return os.environ['SMISK_ENVIRONMENT']
    environment = unsafe_environment
    
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
    
    # Bind
    if len(sys.argv) > 1:
      smisk.bind(sys.argv[1])
      log.info('Listening on %s', sys.argv[1])
    
    # Enable auto-reloading
    if app.autoreload:
      from smisk.autoreload import Autoreloader
      ar = Autoreloader()
      ar.start()
    
    # Run app
    app.run()
  except KeyboardInterrupt:
    pass
  except SystemExit:
    raise
  except:
    try:
      log.critical('died from:', exc_info=True)
    except:
      pass
    try:
      f = open(os.path.join(os.environ['SMISK_APP_DIR'], 'error.log'), 'a')
      try:
        from traceback import print_exc
        print_exc(1000, f)
      finally:
        f.close()
    except:
      pass
    sys.exit(1)
