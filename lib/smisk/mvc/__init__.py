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
from routing import ClassTreeRouter
from ..serialization import serializers

log = logging.getLogger(__name__)


def unique_sorted_modules_of_items(v):
  s = []
  for t in v:
    s.append(t.__module__)
  s = list_unique_wild(s)
  s.sort()
  return s

class Application(smisk.core.Application):
  
  default_content_type = 'application/json'
  '''
  Default output type must be a string.
  '''
  
  serializer = None
  '''Used at runtime'''
  
  output_type = None
  '''Used at runtime'''
  
  output_encoding = None
  '''Used at runtime'''
  
  def __init__(self, *args, **kwargs):
    super(Application, self).__init__(*args, **kwargs)
    logging.basicConfig(
      level=logging.DEBUG,
      format = '%(levelname)-8s %(name)-20s %(message)s',
      datefmt = '%d %b %H:%M:%S'
    )
    self.router = ClassTreeRouter()
  
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
    
    if log.level <= logging.DEBUG:
      log.debug('Active serializers: %s',
        ', '.join(unique_sorted_modules_of_items(serializers.values())) )
      log.debug('Managable types: %s', ', '.join(serializers.keys()))
    log.info('Accepting connections')
  
  def service(self):
    if log.level <= logging.INFO:
      timer = Timer()
    
    # Reset
    self.serializer = None
    self.output_type = None
    self.output_encoding = None
    
    # Find content type and an appropriate serializer
    input_type = self.request.env.get('CONTENT_TYPE', None)
    if input_type is not None:
      input_type = input_type.lower()
      self.serializer = serializers.get(input_type, None)
    self.output_type = input_type
    
    is_POST = False
    if self.request.env['REQUEST_METHOD'] == 'POST':
      is_POST = True
    
    # Parse input
    methodname = None
    args = []
    params = self.request.get
    if is_POST:
      log.debug('Parsing POST request of type %s', repr(input_type))
      if self.serializer is not None:
        (methodname, in_args, in_params) = self.serializer.decode(self.request.input)
        if in_args is not None:
          args = in_args
        if in_params is not None:
          params.update(in_params)
      else:
        params.update(self.request.post)
    
    log.debug('Input: methodname=%s, args=%s, params=%s', methodname, repr(args), repr(params))
    
    # Find and call destination
    resolve_url = self.request.url
    if methodname is not None:
      resolve_url = URL()
      resolve_url.path = methodname.replace('.', '/')
    destination = self.router(resolve_url)
    log.debug('Calling destination %s', repr(destination))
    
    # Process -- call action
    response_st = destination(*args, **params)
    
    # Send any response
    if response_st is not None:
      # Find out if destination did override the output_type
      p = self.response.find_header('Content-Type:')
      if p != -1:
        self.output_type = self.response.headers[p][13:]
        del self.response.headers[p]
        p = self.output_type.find(';')
        if p != -1:
          self.output_type = self.output_type[0:p]
        self.output_type = self.output_type.strip(' ')
      
      # Set content type
      if self.serializer is not None:
        self.output_type = self.serializer.output_type
      if self.output_type is None or self.output_type not in serializers:
        self.output_type = self.default_content_type
      
      # Serialize the response
      try:
        # Make sure we can serialize the response
        if self.serializer is None:
          self.serializer = serializers[self.output_type]
        
        # Encode response
        if isinstance(response_st, dict): 
          response_s = self.serializer.encode(**response_st)
        elif isinstance(response_st, list): 
          response_s = self.serializer.encode(*response_st)
        else:
          response_s = self.serializer.encode(response_st)
        
        # Aquire output encoding
        self.output_encoding = self.serializer.output_encoding
      except KeyError:
        log.warn('No serializer found for %s -- responding with repr() as text/plain', self.output_type)
        self.output_type = 'text/plain'
        response_s = repr(response_st)+"\n"
      
      self.respond(response_s)
    
    # Report performance
    if log.level <= logging.INFO:
      timer.finish()
      url = self.request.url.to_s(scheme=0, user=0, password=0, host=0, port=0)
      log.info('Processed %s in %.3fms', url, timer.time()*1000.0)
  
  
  def respond(self, body):
    # Add headers if the response has not yet begun
    if not self.response.has_begun:
      # Add content-length
      if self.response.find_header('Content-Length:') == -1:
        self.response.headers.append('Content-Length: %d' % len(body))
      # Add content-type
      if self.output_encoding is not None:
        self.response.headers.append('Content-Type: %s; charset=%s' % (self.output_type, self.output_encoding))
      else:
        self.response.headers.append('Content-Type: %s' % self.output_type)
  
    assert(isinstance(body, basestring))
  
    # Write response body
    self.response.write(body)
  
  
  def error(self, typ, val, tb):
    if self.serializer is not None:
      try:
        s = self.serializer.encode_error(typ, val, tb)
        if s is not None:
          status = getattr(val, 'http_code', 500)
          status_name = "Internal Error"
          if status in http.STATUS:
            status_name = http.STATUS[status]
          if status % 500 < 500:
            log.error('Request failed for %s', repr(self.request.url.path), exc_info=(typ, val, tb))
          else:
            log.warn('Request failed for %s -- %s: %s', repr(self.request.url.path), typ.__name__, str(val))
          self.response.headers.append('Status: %d %s' % (status, status_name))
          self.respond(s)
          return
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

