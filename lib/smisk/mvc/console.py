#!/usr/bin/env python
# encoding: utf-8
'''Interactive console aiding in development and management.

Start the console by importing and running its `main()` from a file in your
application top module:

.. python::  
  #!/usr/bin/env python
  from smisk.mvc.console import main
  if __name__ == '__main__':
    main()

The console can also be run directly from the module::

  python -m smisk.mvc.console

'''

import sys, os, time, logging, __builtin__
import code, readline, atexit
from smisk import *
from smisk.mvc.control import *
from smisk.mvc.model import *

class Console(code.InteractiveConsole):
  def __init__(self, locals=None, filename="<console>",
               histfile=os.path.expanduser("~/.console-history")):
    code.InteractiveConsole.__init__(self, locals=locals, filename=filename)
    self.init_history(histfile)
  
  def init_history(self, histfile):
    try:
      import rlcompleter
      readline.parse_and_bind("tab: complete")
      if hasattr(readline, "read_history_file"):
        try:
          readline.read_history_file(histfile)
        except IOError:
          pass
        atexit.register(self.save_history, histfile)
    except ImportError:
      log.info("readline not available")
  
  def save_history(self, histfile):
    readline.set_history_length(1000)
    readline.write_history_file(histfile)
  


def main(app=None,
         appdir=None,
         log_format='\033[1;33m%(levelname)-8s \033[1;31m%(name)-20s\033[0m %(message)s',
         *args, **kwargs):
  '''Console entry point.
  
  Excessive arguments and keyword arguments are passed to `mvc.Application.__init__()`.
  If `app` is already an instance, these extra arguments and keyword arguments
  have no effect.
  
  :Parameters:
    app : Application
      An application type or instance.
    appdir : string
      Application directory. If not defined and running this module directly, the
      current working directory will be used. If not defined and calling this function
      from another module, ``dirname(<__main__ module>.__file__)`` will be used.
    log_format : string
      Custom logging format.
  :rtype: None
  '''
  if appdir is None:
    if 'SMISK_APP_DIR' in os.environ and os.environ['SMISK_APP_DIR']:
      appdir = os.environ['SMISK_APP_DIR']
    else:
      if __name__ == '__main__':
        appdir = os.getcwd()
      else:
        appdir = os.path.dirname(sys.modules['__main__'].__file__)
  appname = os.path.basename(appdir)
  
  # Load application
  if control.root_controller() is None:
    orig_syspath = sys.path
    try:
      sys.path = [os.path.dirname(appdir)]
      m = __import__(appname, globals(), {}, ['*'])
      for k in dir(m):
        try:
          setattr(__builtin__, k, getattr(m, k))
        except:
          pass
    except ImportError, e:
      raise EnvironmentError('Unable to automatically load application. Try to load it '\
        'yourself or provide an absolute appdir with your call to console.main(): %s' % e)
    finally:
      sys.path = orig_syspath
  
  try:
    app = setup(app=app, appdir=appdir, log_format=log_format, *args, **kwargs)
    del log_format
  except:
    sys.stderr.write(format_exc(as_string=True))
    sys.exit(1)
  
  class _ls(object):
    def __call__(self, obj):
      print introspect.format_members(obj, colorize=True)
    def __repr__(self):
      return introspect.format_members(globals(), colorize=True)
    
  
  class _Helper(object):
    def __repr__(self):
      readline_info = ''
      if readline:
        readline_info = 'Readline is active, thus you can use TAB to '\
          'browse and complete Python statements.'
      return '''Interactive Python console with Smisk.

Your application has been loaded and set up. You can now interact with any
component. %(readline)s

Examples:

  ls(object)      List all members and values of any object.

  help(something) Display help for something. For example help(re) to read the
                  manual on the Regular Expressions module.

  run([bind])     Starts your application. Note that if you are not binding to
                  an address but try to run the application as if in a FastCGI
                  environment, this will fail (because this is not a FastCGI
                  environment).

  controllers()   List of installed controllers.

  root_controller()
                  The root controller. You can for example ask it for all
                  available methods by typing: root_controller()()._methods()

  uri_for(node)   Return the URI for any node on the controller tree.
  
  

Type help() for interactive help, or help(object) for help about object.
^D to exit the console.''' % {
    'readline':readline_info
  }
    def __call__(self, *args, **kwargs):
      import pydoc
      return pydoc.help(*args, **kwargs)
  
  # Export locals and globals
  for k,v in locals().iteritems():
    setattr(__builtin__, k, v)
  for k,v in globals().iteritems():
    setattr(__builtin__, k, v)
  
  __builtin__.help = _Helper()
  __builtin__.ls = _ls()
  
  histfile = os.path.expanduser(os.path.join('~', '.%s_console_history' % appname))
  console = Console(locals=locals(), histfile=histfile)
  __builtin__.console = console
  import platform
  console.interact('Smisk interactive console. Python v%s' % platform.python_version())


if __name__ == '__main__':
  main()
