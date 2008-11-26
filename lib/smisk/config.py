# encoding: utf-8
'''User configuration.
'''
import sys, os, logging
from smisk.util.collections import merge_dict
log = logging.getLogger(__name__)

__all__ = ['config', 'config_locations', 'Configuration',
           'configure_logging', 'LOGGING_FORMAT']

# setup check_dirs
if sys.platform == 'win32':
  from win32com.shell import shell, shellcon
  sysconfdir = shell.SHGetSpecialFolderPath(0, shellcon.CSIDL_APPDATA)
else:
  sysconfdir = '/etc'

config_locations = [os.path.join(sysconfdir, 'default'), sysconfdir]
'''Default directories in which to look for configurations files, effective
when using Configuration.load().
'''

def _strip_comments(s):
  while 1:
    a = s.find('/*')
    if a == -1:
      break
    b = s.find('*/', a+2)
    if b == -1:
      break
    s = s[:a] + s[b+2:]
  return s

def _preprocess_input(s):
  s = s.strip()
  if s:
    s = _strip_comments(s)
    if s and s[0] != '{':
      s = '{' + s + '}'
  return s


class Configuration(dict):
  '''Configuration dictionary.
  '''
  
  sources = []
  '''Ordered list of sources used to create this dict.
  '''
  
  default_symbols = {
    'true': True, 'false': False,
    'null': None
  }
  
  defaults = {}
  '''Default values
  '''
  
  filename_ext = '.conf'
  '''Filename extension of configuration files
  '''
  
  logging_key = 'logging'
  '''Name of logging key
  '''
  
  for k in 'CRITICAL FATAL ERROR WARN WARNING INFO NOTSET DEBUG'.split():
    v = getattr(logging, k)
    default_symbols[k] = v
    default_symbols[k.lower()] = v
  
  def __init__(self, *args, **defaults):
    dict.__init__(self, *args, **defaults)
    self.sources = []
    self.filters = []
    self._defaults = defaults
  
  def _get_defaults(self):
    return self._defaults
  
  def _set_defaults(self, d):
    if not isinstance(d, dict):
      raise TypeError('defaults must be a dict')
    self._defaults = d
    self.reload()
  
  defaults = property(_get_defaults, _set_defaults)
  
  def set_default(self, k, v):
    self._defaults[k] = v
    self[k] = v
  
  def __call__(self, name, defaults=None, locations=[], symbols={}, logging_key=None):
    '''Load configuration files from a series of pre-defined locations.
    Returns a list of files that was loaded.
    '''
    log.info('loading named configuration %r', name)
    if isinstance(defaults, dict):
      self.defaults = defaults
    fn = name+self.filename_ext
    paths = []
    files_loaded = []
    for dirname in config_locations:
      paths.append(os.path.join(dirname, fn))
    if sysconfdir in config_locations:
      # /etc/<name>/<name>.conf
      paths.append(os.path.join(sysconfdir, name, fn))
    paths.extend([
      os.path.join('.', fn),
      os.path.join('.', name+'-user'+self.filename_ext),
      os.path.join(os.path.expanduser('~'), fn),
    ])
    if locations:
      for dirname in locations:
        paths.append(os.path.join(dirname, fn))
    for path in paths:
      log.debug('load: trying %s', path)
      if os.path.isfile(path):
        self.load(path, symbols, post_process=False)
        files_loaded.append(path)
    if logging_key is not None:
      self.logging_key = logging_key
    if files_loaded:
      self._post_process()
    return files_loaded
  
  def load(self, path, symbols={}, post_process=True):
    '''Load configuration from file denoted by *path*.
    Returns the dict loaded.
    '''
    f = open(path, 'r')
    try:
      conf = self._loads(path, f.read(), symbols)
    finally:
      f.close()
    if post_process:
      self._post_process()
    return conf
  
  def loads(self, string, symbols={}, post_process=True):
    '''Load configuration from string.
    Returns the dict loaded.
    '''
    load_key = '<string#0x%x>' % hash(string)
    conf = self._loads(load_key, string, symbols)
    if post_process:
      self._post_process()
    return conf
  
  def reload(self):
    '''Reload configuration
    '''
    log.info('reloading configuration')
    reload_paths = []
    self.clear()
    self.update(self.defaults)
    for k,conf in self.sources:
      if k[0] == '<':
        # initially loaded from a string
        self.update(conf)
      else:
        self.load(k, post_process=False)
    self._post_process()
  
  def update(self, b):
    merge_dict(self, b, merge_lists=True)
  
  def add_filter(self, filter):
    '''Add a filter
    '''
    if filter not in self.filters:
      self.filters.append(filter)
  
  def apply_filters(self):
    '''Apply filters.
    '''
    if self.filters:
      log.debug('applying filters %r', self.filters)
      for filter in self.filters:
        filter(self)
  
  def _post_process(self):
    self.apply_filters()
    if self.logging_key:
      self._configure_logging()
    log.info('active configuration: %r', self)
  
  def _configure_logging(self):
    try:
      conf = self[self.logging_key]
      if not isinstance(conf, dict):
        log.warn('logging configuration exists but is not a dict -- skipping')
        return
    except KeyError:
      log.debug('no logging configuration found')
      return
    log.debug('using logging configuration %r', conf)
    configure_logging(conf)
  
  def _loads(self, load_key, string, symbols):
    load_key = intern(load_key)
    syms = self.default_symbols.copy()
    syms.update(symbols)
    string = _preprocess_input(string)
    if string:
      log.info('loading %s', load_key)
      conf = eval(string, syms)
      if not isinstance(conf, dict):
        raise TypeError('configuration %r does not represent a dictionary' % path)
      self.update(conf)
      try:
        for i,v in enumerate(self.sources):
          if v[0] == load_key:
            self.sources[i] = (load_key, conf)
            raise NotImplementedError()
        self.sources.append((load_key, conf))
      except NotImplementedError:
        pass
    else:
      log.debug('skipping empty configuration %s', load_key)
  

config = Configuration()



#---------------------------------------------------------------------------
# Logging configuration routines

LOGGING_DATEFMT = '%Y-%m-%d %H:%M:%S'
LOGGING_FORMAT = '%(asctime)s.%(msecs)03d [%(process)d] %(name)s %(levelname)s: %(message)s'

def configure_logging(conf):
  '''Configure the logging module based on *conf*.
  '''
  setup_root = len(logging.root.handlers) == 0
  # critical section
  logging._acquireLock()
  try:
    if setup_root or 'filename' in conf or 'stream' in conf:
      _configure_logging_root_handler(conf)
    if setup_root or 'format' in conf or 'datefmt' in conf:
      _configure_logging_root_formatter(conf)
    if 'levels' in conf:
      _configure_logging_levels(conf['levels'])
  finally:
    logging._releaseLock()

def _configure_logging_root_handler(conf):
  filename = conf.get('filename')
  if filename:
    handler = logging.FileHandler(filename, conf.get('filemode', 'a'))
  else:
    stream = conf.get('stream', sys.stderr)
    if not hasattr(stream, 'write'):
      # Will raise KeyError for anything else than the two allowed streams
      stream = {'stdout':sys.stdout, 'stderr':sys.stderr}[stream]
    handler = logging.StreamHandler(stream)
  # Replace the handler for the root logger
  logging.root.handlers = [handler]

def _configure_logging_root_formatter(conf):
  try:
    handler = logging.root.handlers[0]
  except IndexError:
    # Uhm, we can't log any warning here, since obviously there's
    # no handlers in the root logger.
    return
  format = conf.get('format', LOGGING_FORMAT)
  datefmt = conf.get('datefmt', LOGGING_DATEFMT)
  handler.setFormatter(logging.Formatter(format, datefmt))

def _configure_logging_levels(levels):
  # reset all loggers level to NOTSET
  for name, logger in logging.Logger.manager.loggerDict.iteritems():
    try:
      logger.setLevel(logging.NOTSET)
    except AttributeError:
      pass
  # assign new levels to specified loggers
  for logger_name, level_name in levels.iteritems():
    if isinstance(level_name, int):
      level = level_name
    else:
      level = logging.getLevelName(level_name.upper())
      if not isinstance(level, int):
        log.warn('unknown logging level %r for logger %r -- skipping', level_name, logger_name)
        continue
    logging.getLogger(logger_name).setLevel(level)


if __name__ == '__main__':
  a = '''
  'logging': {'levels':{'':DEBUG}}
  '''
  b = '''
  "some_key": 456,
  "logging": { /* js comment 1 */
    'format': '%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
    'datefmt': '%H:%M:%S',
    /*
     * js comment 2
     */
    'levels': {
      '': 'INFO',
    }
  }
  '''
  config('config')
  config.loads(a)
  config.loads(b)
  config.reload()
