# encoding: utf-8
import sys, os, logging, logging.config, imp
from copy import copy

import smisk, smisk.core
from smisk.util import *
from smisk.util.timing import Timer
from smisk.inflection import inflection

from mako.lookup import TemplateLookup

from control import *
from exceptions import *
from routing import Router
import http, mime, model
from template import Templates
from constants import *

import modulefinder

# Globals
app = None
router = None
conf = {}
log = logging.getLogger(__name__)

environment = DEVELOPMENT
if 'SMISK_ENVIRONMENT' in os.environ:
  if os.environ['SMISK_ENVIRONMENT'][0] == 'p':
    environment = PRODUCTION
elif not __debug__: # not defined, but PYTHON_OPTIMIZE=YES
  environment = PRODUCTION

# Logging
# May be overridden from configuration
if environment is DEVELOPMENT:
  if __debug__:
    logging.getLogger('').setLevel(logging.DEBUG)
  else:
    logging.getLogger('').setLevel(logging.INFO)
else:
  logging.getLogger('').setLevel(logging.WARNING)
logging.basicConfig(format='[%(asctime)s %(name)s %(levelname)s] %(message)s')
log = logging.getLogger(__name__)


# Rebind Mako filters to the faster Smisk versions
import mako.filters, smisk.core.xml
mako.filters.html_escape = smisk.core.xml.encode
mako.filters.xml_escape = smisk.core.xml.encode
mako.filters.url_escape = smisk.core.URL.encode
mako.filters.url_unescape = smisk.core.URL.decode


class Application(smisk.core.Application):
  # Knowledge about MSIE minimum error message sizes, used in error()
  _msie_error_sizes = {
    400:512, 403:256, 404:512, 405:256, 406:512,
    408:512, 409:512, 410:256, 500:512, 501:512, 505:512
  }
  
  @classmethod
  def main(cls, appdir):
    try:
      app = cls(appdir)
      if len(sys.argv) > 1:
        log.info('Binding to %s', repr(sys.argv[1]))
        smisk.bind(sys.argv[1])
      app.run()
    except KeyboardInterrupt:
      pass
    except:
      log.critical('%s died', repr(cls), exc_info=True)
      raise
  
  
  def __init__(self, appdir, *args, **kwargs):
    super(Application, self).__init__(*args, **kwargs)
    
    appdir = os.path.abspath(appdir)
    
    self.appdir = appdir
    self.controllers = {}
    self.controller_mods = []
    self.model_mods = []
    self.autoreload = True
    self.input_encoding = 'utf-8'
    self.output_encoding = 'utf-8'
    self.templates = Templates(self)
    self.modules = modulefinder.ModuleFinder(
      path = sys.path.extend((
        os.path.join(appdir, 'controllers'),
        os.path.join(appdir, 'models'),
        os.path.join(appdir, 'lib')
      )),
      excludes = sys.path,
      debug = 1
    )
    sys.stdout = sys.stderr
    
    # Set paths
    self.templates.directories = [os.path.join(appdir, 'views')]
    sys.path.append(os.path.join(appdir, 'lib'))
    
    # Register ourselves as THE app
    global app
    app = self
    
    # Create our router
    global router
    router = Router()
    
    self.load_config('application')
    self.load_config(environment)
    
    if self.templates.autoreload is None:
      self.templates.autoreload = self.autoreload
    
    self.load_controllers()
    self.load_models()
  
  
  def load_config(self, name):
    filename = os.path.join(self.appdir, 'config', '%s.py' % name)
    templates = self.templates
    appdir = self.appdir
    global conf
    if os.path.isfile(filename):
      log.info('Loading config/%s.py' % name)
      before_locals = locals().keys()
      execfile(filename, globals(), locals())
      for k,v in locals().iteritems():
        if k not in before_locals and k != 'before_locals':
          conf[k] = v
      log.debug("conf is now %s", repr(conf))
    else:
      log.info('No %s configuration found (config/%s.py)' % (name, name))
  
  
  def load_controllers(self):
    log.info('Loading controllers')
    #mods = self.load_modules_in_dir(os.path.join(self.appdir, 'controllers'), 'index')
    #if mods:
    #  self.controller_mods.extend(mods)
    
    package_name = 'controllers'
    
    package = self.modules.load_package(package_name, os.path.join(self.appdir, 'controllers'))
    log.debug('package = %s', repr(package))
    
    names = []
    
    if package.__path__:
      
      for dir in package.__path__:
        for fn in os.listdir(dir):
          if fn[-3:] == '.py':
            name = fn[:-3]
            if name != '__init__':
              names.append(name)
      
      if names:
        names.sort()
        for name in names:
          fqname = package_name + '.' + name
          m = self.modules.import_module(name, fqname, package)
          log.debug('m = %s', repr(m))
    
  
  
  def load_models(self):
    log.info('Loading models')
    mods = self.load_modules_in_dir(os.path.join(self.appdir, 'models'))
    if mods:
      self.model_mods.extend(mods)
      log.info('Setting up smisk.mvc.model')
      model.setup_all()
  
  
  def load_modules_in_dir(self, path, base_module_name=None):
    modules = []
    if base_module_name is None:
      base_module_name = os.path.basename(path)
    for filename in os.listdir(path):
      if filename[-3:] == '.py':
        name = filename[:-3]
        if name == '__init__':
          name = base_module_name
        #(modFile, modFilename, modDesc) = imp.find_module(modName, [modDir])
        filename = os.path.join(path, filename)
        fp = open(filename, 'rb')
        try:
          mod = imp.load_module(name, fp, filename, ('.py', 'U', 1))
          mod.application = self
          mod.log = logging.getLogger(mod.__name__)
          modules.append(mod)
          log.debug("Loaded %s", repr(mod))
        finally:
          fp.close()
    return modules
  
  
  def application_will_start(self):
    # assign locals to modules
    for mod in self.controller_mods:
      mod.request = self.request
      mod.response = self.response
    global request, response
    request = self.request
    response = self.response
    # Reload template configuration
    self.templates.default_locals
    self.templates.reload_config()
    log.debug('Application is accepting connections')
  
  
  def controller_named(self, name):
    key = name.lower()
    if key not in self.controllers:
      class_name_p = inflection.camelize(inflection.pluralize(name))
      class_name_s = inflection.camelize(inflection.singularize(name))
      names = [class_name_s, class_name_s+"Controller"]
      if class_name_s != class_name_p:
        names += [class_name_p, class_name_p+"Controller"]
      log.debug("Controller lookup for any %s", repr(names))
      if not self.controller_named_r(key, names, Controller):
        raise ControllerNotFound("\"%s\" controller could not be found" % key)
    return self.controllers[key]
  
  
  def controller_named_r(self, key, names, cls):
    for c in cls.__subclasses__():
      if c.__name__ in names:
        self.controllers[key] = c
        log.debug("controller_named_r: found: %s (%s)", c.controller_name(), c.__name__)
        return 1
      if self.controller_named_r(key, names, c):
        return 1
  
  
  def service(self):
    timer = Timer() # xxx optimise this by reusing one timer
    dest = router(self.request.url.path)
    dest_ctrl = None
    dest_action = None
    
    if dest is None:
      raise NotFound('No route to destination')
    
    # Make a copy of dest so to keep the original in pristine form
    dest = copy(dest)
    
    # Find controller
    try:
      dest_ctrl = dest['controller']
      del dest['controller']
    except KeyError:
      raise MVCError('No controller specified. Router mapping is missing a controller.')
    
    # Find action
    try:
      dest_action = dest['action']
      if dest_action and dest_action[0] == '_':
        raise ActionNotFound('%s action could not be found' % repr(dest_action))
      del dest['action']
    except KeyError:
      raise MVCError('No action specified. Router mapping is missing an action.')
    
    # Default application?
    if dest_ctrl is None:
      dest_ctrl = 'application'
    
    # Default action?
    if dest_action == None:
      dest_action = 'index'
    
    # Get the actual controller
    controller = self.controller_named(dest_ctrl)
    dest_ctrl = controller.controller_name() # canonicalize
    
    # Get the actual action
    action = getattr(controller(), dest_action, None)
    if action is None or getattr(action, 'hidden', False) is True:
      raise ActionNotFound("\"%s\" action could not be found in controller %s (%s)" %\
        (dest_action, repr(controller()), repr(controller) ))
    
    # Call action
    if __debug__:
      log.debug("Calling %s.%s(%s)", controller.__name__, dest_action, repr(dest))
    action_returned = action(**dest)
    action_return_type = type(action_returned)
    
    # Render results
    if action_return_type == str:
      # String returned means we do not want a template
      self.response.write(r)
    else:
      # Use a template
      template_fn = getattr(action, 'template', None)
      # If action.template is False nothing should be rendered
      if template_fn is not False:
        self.service_template(template_fn, dest_ctrl, dest_action, controller, action_returned, action_return_type, dest)
      elif __debug__:
        log.debug('Skipping rendering since action.template is False')
    
    # Imformation about time spent servicing this request
    timer.finish()
    log.info('Serviced in %.3fms', timer.time()*1000.0)
  
  
  def service_template(self, template_fn, dest_ctrl, dest_action, controller, action_returned, action_return_type, dest):
    format = 'html' # default
    dest['controller'] = dest_ctrl
    dest['action'] = dest_action
    
    # Figure out template path if not explicitl set
    if template_fn is None:
      if dest_ctrl == 'application':
        # The application controller is special and maps to <template base dir>/<action name>
        template_fn = dest_action
      else:
        # Other controllers map template paths as <template base dir>/<controller name>/<action name>
        template_fn = os.path.join(dest_ctrl, dest_action)
    
    # add controller details
    for k in dir(controller()):
      if k[0] != '_':
        dest[k] = getattr(controller(), k)
    
    # add anything returned by action
    if action_return_type == dict:
      for (k,v) in action_returned.iteritems():
        dest[k] = v
    
    # Map template format from mime-type
    header_index = self.response.find_header('content-type:')
    if header_index != -1:
      content_type = self.response.headers[header_index][13:].strip("\t ").lower()
      semicolon_index = content_type.find(';')
      if semicolon_index != -1:
        content_type = content_type[:semicolon_index].rstrip("\t ")
      if content_type in mime.TYPES:
        format = mime.TYPES[content_type][0] # use first ext
    
    # Render the template
    self.render(template_fn + '.' + format, **dest)
  
  
  def render(self, filename, send=True, **data):
    tpl = self.templates.template_for_uri(filename)
    if send:
      body = tpl.render(**data)
      
      # Add content length header if not added by the application already
      #
      # Discussion: Adding content-length might be a problem: If the action, or the template,
      #             calls this method them selves with send=True, the actual body length will
      #             change but the Content-Type header will not -- client will probably read 
      #             partial response.
      #
      log.debug('self.response=%s', repr(dir(self.response)))
      if not self.response.has_begun and self.response.find_header('content-length:') == -1:
        self.response.headers.append('Content-Length: %d' % len(body))
      
      self.response.write(body)
    else:
      return tpl.render(**data)
  
  
  def error(self, typ, val, tb):
    try:
      log.error('Request failed for %s', repr(self.request.url.path), exc_info=(typ, val, tb))
      if self.templates.render_error(typ, val, tb):
        return
    except:
      log.error('Application error template formatting failed:', exc_info=1)
    super(Application, self).error(typ, val, tb)
  

