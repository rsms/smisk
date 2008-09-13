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
  '''MVC application'''
  
  router_type = ClassTreeRouter
  '''Default router type'''
  
  default_output_encoding = 'utf-8'
  '''Default response character encoding'''
  
  default_media_type = 'application/xhtml+xml'
  
  serializer = None
  '''Used during runtime. Here because we want to use it in error()'''
  
  def __init__(self, *args, **kwargs):
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
    serializer_media_types = serializers.media_types.keys()
    if not self.default_media_type in serializer_media_types:
      if len(serializers.media_types) == 0:
        log.warn('No serializers available!')
      else:
        self.default_media_type = serializers.media_types.keys()[0]
        log.warn('app.default_media_type is not available from current set of serializers'\
                 ' -- setting to first registered serializer: %s', self.default_media_type)
    
    # Info about serializers
    if log.level <= logging.DEBUG:
      log.debug('Active serializers: %s', ', '.join(unique_sorted_modules_of_items(serializers.values())) )
      log.debug('Available media types: %s', repr(serializers.media_types.keys()))
      log.debug('Available filename extensions: %s', repr(serializers.extensions.keys()))
    
    # When we return, accept() in smisk.core is called
    log.info('Accepting connections')
  
  def get_serializer(self):
    '''Return the most appropriate serializer for the current transaction'''
    # Try filename extension
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
    # Default serializer. Worst case scenario: return None
    return serializers.media_types.get(self.default_media_type, None)
  
  def service(self):
    # Clear any old serializer
    self.serializer = None
    
    if log.level <= logging.INFO:
      timer = Timer()
    
    # Setup context
    self.serializer = self.get_serializer()
    if self.serializer is None:
      raise Exception('No serializer available!')
    
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
    
    if log.level <= logging.DEBUG:
      log.debug('Input: methodname=%s, args=%s, params=%s', methodname, repr(args), repr(params))
    
    # Find and call destination
    resolve_url = self.request.url
    if methodname is not None:
      resolve_url = URL()
      resolve_url.path = methodname.replace('.', '/')
    else:
      elen = len(self.serializer.extension)+1
      if resolve_url.path[-elen:] == '.'+self.serializer.extension:
        resolve_url.path = resolve_url.path[:-elen]
      log.debug('resolve_url.path=%s', resolve_url.path)
    destination = self.router(resolve_url)
    log.debug('Calling destination %s', repr(destination))
    
    # Process -- call action
    rsp = destination(*args, **params)
    
    # Send any response
    if rsp is not None:
      # Encode response
      if isinstance(rsp, dict): 
        rsp = self.serializer.encode(**rsp)
      elif isinstance(rsp, list): 
        rsp = self.serializer.encode(*rsp)
      else:
        rsp = self.serializer.encode(rsp)
      
      # Make sure rsp is a string
      assert(isinstance(rsp, basestring))
      
      # Add headers if the response has not yet begun
      if not self.response.has_begun:
        # Add Content-Length header
        if self.response.find_header('Content-Length:') == -1:
          self.response.headers.append('Content-Length: %d' % len(rsp))
        # Add Content-Type header
        self.serializer.add_content_type_header(self.response)
      
      # Write response
      self.response.write(rsp)
    
    # Report performance
    if log.level <= logging.INFO:
      timer.finish()
      url = self.request.url.to_s(scheme=0, user=0, password=0, host=0, port=0)
      log.info('Processed %s in %.3fms', url, timer.time()*1000.0)
  
  def error(self, typ, val, tb):
    if self.serializer is not None:
      try:
        rsp = self.serializer.encode_error(typ, val, tb)
        if rsp is not None:
          status = getattr(val, 'http_code', 500)
          if status % 500 < 500:
            log.error('Request failed for %s', repr(self.request.url.path), exc_info=(typ, val, tb))
          else:
            log.warn('Request failed for %s -- %s: %s', repr(self.request.url.path), typ.__name__, str(val))
          if not self.response.has_begun:
            status_name = "Internal Error"
            if status in http.STATUS:
              status_name = http.STATUS[status]
            self.response.headers = ['Status: %d %s' % (status, status_name)]
            self.response.headers.append('Content-Length: %d' % len(rsp))
            self.serializer.add_content_type_header(self.response)
          self.response.write(rsp)
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

