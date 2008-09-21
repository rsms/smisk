# encoding: utf-8
import sys, os, logging
from types import DictType
import smisk, smisk.core
import http, control

from smisk.core import URL
from smisk.util import *
from smisk.serialization import serializers

from control import Controller
from model import Entity
from template import Templates
from routing import Router
from exceptions import *

log = logging.getLogger(__name__)
application = None
request = None
response = None

class Response(smisk.core.Response):
  format = None
  '''
  Any value which is a valid key of the serializers.extensions dict.
  
  :type: string
  '''
  
  status = http.OK
  ''':type: smisk.mvc.http.Status'''


class Application(smisk.core.Application):
  '''MVC application'''
  
  default_output_encoding = 'utf-8'
  '''
  Default response character encoding.
  
  :type: string
  '''
  
  default_format = 'html'
  
  templates = None
  ''':type: Templates'''
  
  autoreload = False
  ''':type: bool'''
  
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
  
  def __init__(self,
               log_level=logging.INFO,
               autoreload=False,
               etag=None, 
               router=None,
               templates=None,
               *args, **kwargs):
    self.response_class = Response
    super(Application, self).__init__(*args, **kwargs)
    
    logging.basicConfig(
      level=log_level,
      format = '%(levelname)-8s %(name)-20s %(message)s',
      datefmt = '%d %b %H:%M:%S'
    )
    
    self.etag = etag
    self.autoreload = autoreload
    
    if router is None:
      self.routes = Router()
    else:
      self.routes = router
    
    if templates is None:
      self.templates = Templates(app=self)
    else:
      self.templates = templates
  
  
  def application_will_start(self):
    # Make sure the router has a reference to to app
    self.routes.app = self
    
    # Setup ETag
    if self.etag is not None and isinstance(self.etag, basestring):
      import hashlib
      self.etag = getattr(hashlib, self.etag)
    
    # Initialize modules which need access to app, request and response
    modules = find_modules_for_classtree(Controller)
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
    
    # Check so the default media type really has an available serializer
    serializer_exts = serializers.extensions.keys()
    if not self.default_format in serializer_exts:
      if len(serializers.extensions) == 0:
        log.warn('No serializers available!')
      else:
        self.default_format = serializers.extensions.keys()[0]
        log.warn('app.default_format is not available from the current set of serializers'\
                 ' -- setting to first registered serializer: %s', self.default_format)
    
    # Check templates config
    if self.templates:
      if not self.templates.directories:
        self.templates.directories = [os.path.join(os.environ['SMISK_APP_DIR'], 'templates')]
      if self.templates.autoreload is None:
        self.templates.autoreload = self.autoreload
    
    # Info about serializers
    if log.level <= logging.DEBUG:
      log.debug('Serializers: %s', ', '.join(unique_sorted_modules_of_items(serializers.values())) )
      log.debug('Serializer media types: %s', ', '.join(serializers.media_types.keys()))
      log.debug('Serializer formats: %s', ', '.join(serializers.extensions.keys()))
      log.debug('Template directories: %s', ', '.join(self.templates.directories))
    
    # When we return, accept() in smisk.core is called
    log.info('Accepting connections')
  
  def _run(self):
    if self.autoreload:
      from smisk.autoreload import Autoreloader
      while 1:
        ar = Autoreloader()
        ar.start()
        smisk.core.Application.run(self)
        sys.modules = default_sys_modules.copy()
    else:
      smisk.core.Application.run(self)
  
  def response_serializer(self):
    '''
    Return the most appropriate serializer for handling response encoding.
    
    :return: The most appropriate serializer
    :rtype:  Serializer
    '''
    # Overridden by explicit response.format?
    if self.response.format is not None:
      # Should fail if not exists
      return serializers.extensions[self.response.format]
    
    # Overridden by explicit Content-Type header?
    p = self.response.find_header('Content-Type:')
    if p != -1:
      content_type = self.response.headers[p][13:].strip("\t ").lower()
      p = content_type.find(';')
      if p != -1:
        content_type = content_type[:p].rstrip("\t ")
      if content_type in serializers.media_types:
        return serializers.media_types[content_type]
    
    # Try filename extension
    if self.request.url.path.rfind('.') != -1:
      filename = os.path.basename(self.request.url.path)
      p = filename.rfind('.')
      if p != -1:
        ext = filename[p+1:]
        if ext in serializers.extensions.keys():
          return serializers.extensions[ext]
    
    # Try media type
    default_serializer = None
    accept_types = self.request.env.get('HTTP_ACCEPT', None)
    if accept_types is not None:
      available_types = serializers.media_types.keys()
      vv = []
      highq = []
      for media in accept_types.split(','):
        p = media.find(';')
        if p != -1:
          pp = media.find('q=', p)
          if pp != -1:
            q = int(float(media[pp+2:])*100.0)
            media = media[:p]
            vv.append([media, q])
            if q == 100:
              highq.append(media)
            continue
        qual = 100
        if media == '*/*':
          qual = 0
        elif '/*' in media:
          qual = 50
        else:
          highq.append(media)
        vv.append([media, qual])
      vv.sort(lambda a,b: b[1] - a[1])
      default_serializer = serializers.extensions.get(self.default_format, None)
      if default_serializer.media_type in highq:
        return default_serializer
      for v in vv:
        if v[0] in available_types:
          return serializers.media_types[v[0]]
    
    # Default serializer (Worst case scenario: return None)
    return default_serializer
  
  
  def parse_request(self):
    '''
    Parses the request, involving appropriate serializer if needed.
    
    :returns: (list arguments, dict parameters)
    :rtype:   tuple
    '''
    args = []
    params = self.request.get
    
    if self.request.env['REQUEST_METHOD'] == 'POST':
      content_type = self.request.env.get('CONTENT_TYPE', '').lower()
      if content_type == 'application/x-www-form-urlencoded' or len(content_type) == 0:
        # Standard urlencoded content
        params.update(self.request.post)
      else:
        # Different kind of content
        serializer = serializers.media_types.get(content_type, None)
        
        # Parse content
        if serializer is not None:
          content_length = int(self.request.env.get('CONTENT_LENGTH', -1))
          (eargs, eparams) = serializer.decode(self.request.input, content_length)
          if eargs is not None:
            args.extend(eargs)
          if eparams is not None:
            params.update(eparams)
        else:
          log.info('No serializer found for request type "%s"', content_type)
    
    return (args, params)
  
  
  def call_action(self, args, params):
    '''
    Resolves and calls the appropriate action, passing args and params to it.
    
    :returns: Response structure or None
    :rtype:   dict
    '''
    # Find destination or return None
    destination, args, params = self.routes(self.request.url, args, params)
    
    # Call action
    if log.level <= logging.DEBUG:
      log.debug('Calling destination %s', destination)
    return destination, destination(*args, **params)
  
  
  def encode_response(self, rsp, template):
    encoding = self.default_output_encoding
    
    # No input at all
    if rsp is None:
      if template:
        return template.render_unicode().encode(encoding)
      return None
    
    # If rsp is already a string, we do not process it further
    if isinstance(rsp, basestring):
      return rsp
    
    # Make sure rsp is a dict
    if not isinstance(rsp, dict):
      raise Exception('actions must return a dict, string or None -- not %s', type(rsp))
    
    # Use template as serializer, if available
    if template:
      return template.render_unicode(**rsp).encode(encoding)
    
    # If we do not have a template, we use a standard serializer
    if self.serializer is None:
      self.serializer = self.response_serializer()
      if self.serializer is None:
        raise Exception('no serializer available')
    return self.serializer.encode(**rsp)
  
  
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
      self.serializer.add_content_type_header(self.response)
      # Add ETag
      if self.etag is not None and len(rsp) > 0 and self.response.find_header('ETag:') == -1:
        h = self.etag(''.join(self.response.headers))
        h.update(rsp)
        self.response.headers.append('ETag: "%s"' % h.hexdigest())
    
    # Send body
    assert(isinstance(rsp, basestring))
    self.response.write(rsp)
  
  
  def service(self):
    if log.level <= logging.INFO:
      timer = Timer()
    
    # Reset response serializer, as it's used in error()
    self.serializer = None
    self.response.format = None
    self.response.status = http.OK
    self.destination = None
    self.template = None
    
    # Parse request (and decode if needed)
    req_args, req_params = self.parse_request()
    
    # Add "private" cache control directive.
    # As most actions will generate different output depending on variables like 
    # client, time and data state, we need to tell facilities between us to, and
    # including, the client the content is private.
    self.response.headers.append('Cache-Control: private')
    
    # Call the action which might generate a response object: rsp
    self.destination, rsp = self.call_action(req_args, req_params)
    
    # Aquire template
    if self.template is None and self.templates is not None:
      self.template = self.template_for_path(os.path.join(*self.destination.path))
    
    # Encode response
    rsp = self.encode_response(rsp, self.template)
    
    # Return a response to the client and thus completing the transaction.
    self.send_response(rsp)
    
    # Report performance
    if log.level <= logging.INFO:
      timer.finish()
      uri = None
      if self.destination is not None:
        uri = '.'.join(self.destination.path)
        if self.serializer is not None:
          uri += ':' + self.serializer.extension
      else:
        uri = self.request.url.to_s(scheme=0, user=0, password=0, host=0, port=0)
      log.info('Processed %s in %.3fms', uri, timer.time()*1000.0)
  
  
  def template_for_path(self, path):
    return self.template_for_uri(self.template_uri_for_path(path))
  
  
  def template_uri_for_path(self, path):
    if self.serializer is None:
      self.serializer = self.response_serializer()
    return path + '.' + self.serializer.extension
  
  
  def template_for_uri(self, uri):
    if log.level <= logging.DEBUG:
      log.debug('Looking for template %s', uri)
    return self.templates.template_for_uri(uri, exc_if_not_found=False)
  
  
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
      
      # Try to use a serializer
      if self.serializer is None:
        try:
          self.serializer = self.response_serializer()
        except:
          pass
      
      # Set format if a serializer was found
      if self.serializer is not None:
        format = self.serializer.extension
      
      # HTTP exception has a bound action we want to call
      if isinstance(val, http.HTTPExc):
        params = val(self)
      
      # Try to use templating or serializer
      rsp = self.templates.render_error(status, format, params, typ, val, tb)
      if rsp is None and self.serializer is not None:
        if not params or type(params) is not DictType:
          params = {'code': status.code, 'message': status.name}
        rsp = self.serializer.encode_error(status, params, typ, val, tb)
      
      # Send response
      if rsp is not None:
        # Set headers
        if not self.response.has_begun:
          if self.response.find_header('Content-Length:') == -1:
            self.response.headers.append('Content-Length: %d' % len(rsp))
          if status.is_error and self.response.find_header('Cache-Control:') == -1:
            self.response.headers.append('Cache-Control: no-cache')
          if self.serializer is not None:
            self.serializer.add_content_type_header(self.response)
        # Write body (and send headers if not yet sent)
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
  ``Application.current()`` if there is an application. Otherwise, a new
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
  # Make sure SMISK_APP_DIR is set correctly
  if 'SMISK_APP_DIR' not in os.environ:
    if appdir is None:
      try:
        appdir = os.path.abspath(os.path.dirname(sys.modules['__main__'].__file__))
      except:
        appdir = os.path.abspath('.')
    os.environ['SMISK_APP_DIR'] = appdir
  try:
    # Aquire app
    if app is None:
      app = Application.current()
      if app is None:
        app = Application(*args, **kwargs)
    elif type(app) is type:
      if not issubclass(app, smisk.core.Application):
        raise ValueError('app is not a subclass of smisk.core.Application')
      app = app(*args, **kwargs)
    elif not isinstance(app, smisk.core.Application):
      raise ValueError('app is not an instance of smisk.core.Application')
    
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
    log.critical('died from:', exc_info=True)
    sys.exit(1)
