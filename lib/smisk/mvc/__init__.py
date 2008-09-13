# encoding: utf-8
import sys, os, logging
import smisk, smisk.core
import http
from smisk.core import URL
from smisk.util import *
from smisk.util.timing import Timer
from control import Controller
from model import Entity
from exceptions import *
from routing import ClassTreeRouter, MethodNotFound
from ..serialization import serializers

log = logging.getLogger(__name__)


def unique_sorted_modules_of_items(v):
  s = []
  for t in v:
    s.append(t.__module__)
  s = list_unique_wild(s)
  s.sort()
  return s


class Response(smisk.core.Response):
  format = None
  '''
  Any value which is a valid key of the serializers.extensions dict.
  
  :type: string
  '''


class Application(smisk.core.Application):
  '''MVC application'''
  
  router_type = ClassTreeRouter
  '''Default router type'''
  
  default_output_encoding = 'utf-8'
  '''Default response character encoding'''
  
  default_format = 'html'
  
  serializer = None
  '''Used during runtime. Here because we want to use it in error()'''
  
  def __init__(self, *args, **kwargs):
    self.response_class = Response
    super(Application, self).__init__(*args, **kwargs)
    logging.basicConfig(
      level=logging.DEBUG,
      format = '%(levelname)-8s %(name)-20s %(message)s',
      datefmt = '%d %b %H:%M:%S'
    )
    self.router = self.router_type()
  
  
  def application_will_start(self):
    # Make sure the router has a reference to to app
    self.router.app = self
    
    # Initialize modules which need access to app, request and response
    modules = find_modules_for_classtree(Controller)
    modules.extend(find_modules_for_classtree(Entity))
    for m in modules:
      log.debug('Initializing app module %s', m.__name__)
      m.app = self
      m.request = self.request
      m.response = self.response
    
    # Check so the default media type really has an available serializer
    serializer_exts = serializers.extensions.keys()
    if not self.default_format in serializer_exts:
      if len(serializers.extensions) == 0:
        log.warn('No serializers available!')
      else:
        self.default_format = serializers.extensions.keys()[0]
        log.warn('app.default_format is not available from the current set of serializers'\
                 ' -- setting to first registered serializer: %s', self.default_format)
    
    # Info about serializers
    if log.level <= logging.DEBUG:
      log.debug('Serializers: %s', ', '.join(unique_sorted_modules_of_items(serializers.values())) )
      log.debug('Serializer media types: %s', repr(serializers.media_types.keys()))
      log.debug('Serializer formats: %s', repr(serializers.extensions.keys()))
    
    # When we return, accept() in smisk.core is called
    log.info('Accepting connections')
  
  
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
    accept_types = self.request.env.get('HTTP_ACCEPT', None)
    if accept_types is not None:
      available_types = serializers.media_types.keys()
      vv = []
      for media in accept_types.split(','):
        p = media.find(';')
        if p != -1:
          pp = media.find('q=', p)
          if pp != -1:
            vv.append([media[:p], int(float(media[pp+2:])*100.0)])
            continue
        qual = 100
        if media == '*/*':
          qual = 0
        elif '/*' in media:
          qual = 50
        vv.append([media, qual])
      vv.sort(lambda a,b: b[1] - a[1])
      for v in vv:
        if v[0] in available_types:
          return serializers.media_types[v[0]]
    
    # Default serializer (Worst case scenario: return None)
    return serializers.extensions.get(self.default_format, None)
  
  
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
    destination = self.router(self.request.url)
    
    # Call action
    if log.level <= logging.DEBUG:
      log.debug('Calling destination %s', repr(destination))
    return destination(*args, **params)
  
  
  def send_response(self, rsp):
    # Empty rsp
    if rsp is None:
      # The action might have sent content using low-level functions,
      # so we need to confirm the response has not yet started and 
      # a custom content length header has not been set.
      if not self.response.has_begun and self.response.find_header('Content-Length:') == -1:
        self.response.headers.append('Content-Length: 0')
      return
    
    # If rsp is not yet a string, we need to serialize it
    if not isinstance(rsp, basestring):
      # Aquire appropriate serializer
      self.serializer = self.response_serializer()
      if self.serializer is None:
        raise Exception('no serializer available')
      
      # Serialize rsp
      if not isinstance(rsp, dict):
        rsp = {'rsp':rsp}
      rsp = self.serializer.encode(**rsp)
    
    # Add headers if the response has not yet begun
    if not self.response.has_begun:
      # Add Content-Length header
      if self.response.find_header('Content-Length:') == -1:
        self.response.headers.append('Content-Length: %d' % len(rsp))
      # Add Content-Type header
      self.serializer.add_content_type_header(self.response)
    
    # Send body
    assert(isinstance(rsp, basestring))
    self.response.write(rsp)
  
  
  def service(self):
    if log.level <= logging.INFO:
      timer = Timer()
    
    # Reset response serializer, as it's used in error()
    self.serializer = None
    self.response.format = None
    
    # Parse request (and decode if needed)
    (req_args, req_params) = self.parse_request()
    
    # Add "private" cache control directive.
    # As most actions will generate different output depending on variables like 
    # client, time and data state, we need to tell facilities between us to, and
    # including, the client the content is private.
    self.response.headers.append('Cache-Control: private')
    
    # Call the action which might generate a response object: rsp
    rsp = self.call_action(req_args, req_params)
    
    # Return a response to the client and thus completing the transaction.
    self.send_response(rsp)
    
    # Report performance
    if log.level <= logging.INFO:
      timer.finish()
      url = self.request.url.to_s(scheme=0, user=0, password=0, host=0, port=0)
      log.info('Processed %s in %.3fms', url, timer.time()*1000.0)
  
  
  def error(self, typ, val, tb):
    try:
      status = getattr(val, 'http_code', 500)
      is_error = status % 500 < 100
      rsp = None
      status_name = "Internal Error"
      if status in http.STATUS:
        status_name = http.STATUS[status]
      
      # Log
      if is_error:
        log.error('%d Request failed for %s', status, repr(self.request.url.path), exc_info=(typ, val, tb))
      else:
        log.warn('Request failed for %s -- %s: %s', repr(self.request.url.path), typ.__name__, str(val))
      
      # Try to use a serializer
      if self.serializer is None:
        try:
          self.serializer = self.response_serializer()
        except:
          pass
      
      # Build response body
      if self.serializer is not None:
        rsp = self.serializer.encode_error(typ, val, tb)
        
      # Send response
      if rsp is not None:
        # Set headers
        if not self.response.has_begun:
          self.response.headers = [
            'Status: %d %s' % (status, status_name),
            'Content-Length: %d' % len(rsp)
          ]
          if is_error:
            self.response.headers.append('Cache-Control: no-cache')
          if self.serializer is not None:
            self.serializer.add_content_type_header(self.response)
        # Write body (and send headers if not yet sent)
        self.response.write(rsp)
        # We're done.
        return
      
      # No rsp or error, so let smisk.core.Application.error() handle the response
    except:
      log.error('Failed to send error using serializer %s', repr(self.serializer), exc_info=1)
    log.error('Request failed for %s', repr(self.request.url.path), exc_info=(typ, val, tb))
    super(Application, self).error(typ, val, tb)
  


def main(cls=Application):
  if 'SMISK_APP_DIR' not in os.environ:
    os.environ['SMISK_APP_DIR'] = os.path.abspath('.')
  
  # Create app and start it
  try:
    app = cls()
    if len(sys.argv) > 1:
      smisk.bind(sys.argv[1])
      log.info('Listening on %s', sys.argv[1])
    app.run()
  except KeyboardInterrupt:
    pass
  except:
    log.critical('%s died', repr(cls), exc_info=True)
    sys.exit(1)
