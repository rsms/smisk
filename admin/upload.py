import urllib2, os, sys
from ConfigParser import SafeConfigParser

class PyPI(object):
  """docstring for PyPI"""
  def __init__(self):
    super(PyPI, self).__init__()
    self.cfg = SafeConfigParser()
    try:
      self.cfg.read(os.path.expanduser('~/.pypirc'))
    except:
      raise Exception('~/.pypirc must be present and have the server-login section.')
  
  def upload():  
    
    auth_handler = urllib2.HTTPBasicAuthHandler()
    auth_handler.add_password(realm='pypi',
                              uri='http://pypi.python.org/pypi',
                              user=cfg.get('server-login', 'username'),
                              passwd=cfg.get('server-login', 'password'))
    urllib2.install_opener(urllib2.build_opener(auth_handler))

    urllib2.urlopen('http://pypi.python.org/pypi')
