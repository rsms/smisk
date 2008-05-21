# encoding: utf-8
import sys, os, logging
import smisk, smisk.core
from smisk.core import URL
from smisk.util import *
from control import Controller
from exceptions import *
from routing import ClassTreeRouter

log = logging.getLogger(__name__)


class Application(smisk.core.Application):
  
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
    log.debug('modules=%s', modules)
    for m in modules:
      m.app = self
      m.request = self.request
      m.response = self.response
    
    log.info('Accepting connections')
  
  def service(self):
    from smisk.util.timing import Timer
    timer = Timer()
    
    # Find and call action
    action = self.router(self.request.url)
    log.debug('Calling action %s', repr(action))
    response_body = action.__call__()
    
    # Handle response body
    if response_body is not None:
      # Serialize to string if not already a string
      if not isinstance(response_body, str):
        log.debug('xxx todo: render %s using a serializer. for example json, yaml, xml, plist or pickle', repr(response_body))
        response_body = str(response_body)
      
      # At this point, response_body must be a string
      if not self.response.has_begun:
        self.response.headers.append('Content-Length: %d' % len(response_body))
      self.response.write(response_body)
    
    # Report performance
    timer.finish()
    log.info('Serviced in %.3fms', timer.time()*1000.0)
  

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
