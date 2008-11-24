# encoding: utf-8
'''User configuration.
'''
import sys, os, logging, time, re
from smisk.util.collections import merge_dict
log = logging.getLogger(__name__)

__all__ = ['config', 'config_locations', 'Configuration']

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

COMMENTS_RE = re.compile('(?:\n[\t ]*#.*\n|/\*+[\t ]*[^\*]*[\t ]*\*+/)', re.M|re.I)

class Configuration(dict):
  '''Configuration dictionary.
  '''
  
  sources = []
  '''Ordered list of sources used to create this dict.
  '''
  
  default_symbols = {
    'true': True, 'false': False,
    'yes': True, 'no': False,
    'null': None
  }
  
  defaults = {}
  '''Default values
  '''
  
  for k in 'CRITICAL DEBUG ERROR FATAL INFO NOTSET WARN WARNING'.split():
    v = getattr(logging, k)
    default_symbols[k] = v
    default_symbols[k.lower()] = v
  
  def __init__(self, *args, **defaults):
    dict.__init__(self, *args, **defaults)
    self.sources = []
    self._defaults = defaults
  
  def _get_defaults(self):
    return self._defaults
  
  def _set_defaults(self, d):
    if not isinstance(d, dict):
      raise TypeError('defaults must be a dict')
    self._defaults = d
    self.reload()
  
  defaults = property(_get_defaults, _set_defaults)
  
  def __call__(self, name, locations=[], symbols={}, logging_key='logging', fext='.conf'):
    '''Load configuration files from a series of pre-defined locations.
    '''
    fn = name+fext
    paths = []
    for dirname in config_locations:
      paths.append(os.path.join(dirname, fn))
    if sysconfdir in config_locations:
      # /etc/<name>/<name>.conf
      paths.append(os.path.join(sysconfdir, name, fn))
    paths.extend([
      os.path.join('.', fn),
      os.path.join('.', name+'-user'+fext),
      os.path.join(os.path.expanduser('~'), fn),
    ])
    if locations:
      for dirname in locations:
        paths.append(os.path.join(dirname, fn))
    for path in paths:
      log.debug('load: trying %s', path)
      if os.path.isfile(path):
        self.load_file(path, symbols)
    
    if logging_key:
      self.setup_logging(logging_key)
  
  def setup_logging(self, key='logging'):
    try:
      logging_conf = self[key]
      if not isinstance(logging_conf, dict):
        log.warn('logging configuration is not a dict -- skipping')
        return
    except KeyError:
      log.debug('no logging configuration found')
      return
    log.debug('using logging configuration %r', logging_conf)
  
  def load_file(self, path, symbols={}):
    '''Load configuration from file denoted by `path`.
    '''
    f = open(path, 'r')
    try:
      return self._loads(path, f.read(), symbols)
    finally:
      f.close()
  
  def loads(self, string, symbols={}):
    '''Load configuration from string.
    '''
    load_key = '<string#0x%x>' % hash(string)
    return self._loads(load_key, string, symbols)
  
  def reload(self):
    log.info('reloading configuration')
    reload_paths = []
    self.clear()
    self.update(self.defaults)
    for k,conf in self.sources:
      if k[0] == '<':
        # initially loaded from a string
        self.update(conf)
      else:
        self.load_file(k)
  
  def update(self, b):
    merge_dict(self, b, merge_lists=True)
  
  def _preprocess_input(self, string):
    string = string.strip()
    if string:
      string = COMMENTS_RE.sub('\n', string)
      if string[0] != '{':
        string = '{' + string + '}'
    return string
  
  def _loads(self, load_key, string, symbols):
    load_key = intern(load_key)
    syms = self.default_symbols.copy()
    syms.update(symbols)
    string = self._preprocess_input(string)
    if string:
      log.info('loading %s', load_key)
      conf = eval(string, syms)
      if not isinstance(conf, dict):
        raise TypeError('configuration %r must contain a dictionary' % path)
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

if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  b = '''
  "some_key": 456,
  "logging": {
    "": "INFO",
  }
  '''
  config('config')
  log.info('config=%r', config)
  config.loads(b)
  log.info('config=%r', config)
  config.reload()
  log.info('config=%r', config)
