# encoding: utf-8
'''Program main routine helpers.
'''
import sys, os, logging, signal, smisk.core
from smisk.config import config as _config

__all__ = ['setup_appdir', 'main_cli_filter', 'handle_errors_wrapper']
log = logging.getLogger(__name__)

def absapp(application, default_app_type=smisk.core.Application, *args, **kwargs):
  '''Returns an application instance or raises an exception if not possible.
  '''
  if not application:
    application = smisk.core.Application.current
    if not application:
      application = default_app_type(*args, **kwargs)
  elif type(application) is type:
    if not issubclass(application, smisk.core.Application):
      raise ValueError('application is not a subclass of smisk.core.Application')
    return application(*args, **kwargs)
  elif not isinstance(application, smisk.core.Application):
    raise ValueError('%r is not an instance of smisk.core.Application' % application)
  return application


def setup_appdir(appdir=None):
  if 'SMISK_APP_DIR' not in os.environ:
    if appdir is None:
      try:
        appdir = os.path.dirname(sys.modules['__main__'].__file__)
      except:
        raise EnvironmentError('unable to calculate SMISK_APP_DIR because: %s' % sys.exc_info())
  if appdir is not None:
    os.environ['SMISK_APP_DIR'] = os.path.abspath(appdir)
  return os.environ['SMISK_APP_DIR']


def main_cli_filter(appdir=None, bind=None, forks=None):
  '''Command Line Interface parser used by `main()`.
  '''
  forks_defaults_to = bind_defaults_to = appdir_defaults_to = ' Not set by default.'
  
  if appdir:
    appdir_defaults_to = ' Defaults to "%s".' % appdir
  
  if isinstance(bind, basestring):
    bind_defaults_to = ' Defaults to "%s".' % bind
  else:
    bind = None
  
  if forks:
    forks_defaults_to = ' Defaults to "%s".' % forks
  
  from optparse import OptionParser
  parser = OptionParser(usage="usage: %prog [options]")
  
  parser.add_option("-d", "--appdir",
                    dest="appdir",
                    help='Set the application directory.%s' % appdir_defaults_to,
                    action="store",
                    type="string",
                    metavar="PATH",
                    default=appdir)
  
  parser.add_option("-b", "--bind",
                    dest="bind",
                    help='Start a stand-alone process, listening for FastCGI connection on '\
                         'ADD, which can be a TCP/IP address with out without host or a UNIX '\
                         'socket (named pipe on Windows). For example "localhost:5000", '\
                         '"/tmp/my_process.sock" or ":5000".%s' % bind_defaults_to,
                    metavar="ADDR",
                    action="store",
                    type="string",
                    default=bind)
  
  parser.add_option("-c", "--forks",
                    dest="forks",
                    help='Set number of childs to fork.%s' % forks_defaults_to,
                    metavar="N",
                    type="int",
                    default=forks)
  
  opts, args = parser.parse_args()
  
  # Make sure empty values are None
  if not opts.bind:
    opts.bind = None
  if not opts.appdir:
    opts.appdir = None
  if not opts.forks:
    opts.forks = None
  
  return opts.appdir, opts.bind, opts.forks


def handle_errors_wrapper(fnc, error_cb=sys.exit, abort_cb=None, *args, **kwargs):
  '''Call `fnc` catching any errors and writing information to ``error.log``.
  
  ``error.log`` will be written to, or appended to if it aldready exists,
  ``ENV["SMISK_LOG_DIR"]/error.log``. If ``SMISK_LOG_DIR`` is not set,
  the file will be written to ``ENV["SMISK_APP_DIR"]/error.log``.
  
  * ``KeyboardInterrupt`` is discarded/passed, causing a call to `abort_cb`,
    if set, without any arguments.
  
  * ``SystemExit`` is passed on to Python and in normal cases causes a program
    termination, thus this function will not return.
  
  * Any other exception causes ``error.log`` to be written to and finally
    a call to `error_cb` with a single argument; exit status code.
  
  :param  error_cb:   Called after an exception was caught and info 
                               has been written to ``error.log``. Receives a
                               single argument: Status code as an integer.
                               Defaults to ``sys.exit`` causing normal program
                               termination. The returned value of this callable
                               will be returned by `handle_errors_wrapper` itself.
  :type   error_cb:   callable
  :param  abort_cb:   Like `error_cb` but instead called when
                      ``KeyboardInterrupt`` was raised.
  :type   abort_cb:   callable
  :rtype: object
  '''
  try:
    # Run the wrapped callable
    return fnc(*args, **kwargs)
  except KeyboardInterrupt:
    if abort_cb:
      return abort_cb()
  except SystemExit:
    raise
  except:
    # Write to error.log
    try:
      log_dir = os.environ.get('SMISK_LOG_DIR', os.environ.get(os.environ['SMISK_APP_DIR'], '.'))
      f = open(os.path.join(log_dir, 'error.log'), 'a')
      try:
        from traceback import print_exc
        from datetime import datetime
        f.write(datetime.now().isoformat())
        f.write(" [%d] " % os.getpid())
        print_exc(1000, f)
      finally:
        f.close()
    except:
      pass
    # Call error callback
    if error_cb:
      return error_cb(1)


class Main(object):
  default_app_type = smisk.core.Application
  _is_set_up = False
  
  def __call__(self, application=None, appdir=None, bind=None, forks=None, handle_errors=True, cli=True, config=None, *args, **kwargs):
    '''Helper for setting up and running an application.
    '''
    if cli:
      appdir, bind, forks = main_cli_filter(appdir=appdir, bind=bind, forks=forks)
    
    # Setup
    if handle_errors:
      application = handle_errors_wrapper(self.setup, application=application, appdir=appdir, config=config, *args, **kwargs)
    else:
      application = self.setup(application=application, appdir=appdir, config=config, *args, **kwargs)
    
    # Run
    return self.run(bind=bind, application=application, forks=forks, handle_errors=handle_errors)
  
  
  def setup(self, application=None, appdir=None, config=None, *args, **kwargs):
    '''Helper for setting up an application.
    Returns the application instance.
    
    Only the first call is effective.
    '''
    if self._is_set_up:
      return smisk.core.Application.current
    self._is_set_up = True
    
    setup_appdir(appdir)
    
    # Load config
    if config:
      prev_cwd = os.getcwd()
      os.chdir(os.environ['SMISK_APP_DIR'])
      try:
        _config(config)
      finally:
        os.chdir(prev_cwd)
    
    return absapp(application, self.default_app_type, *args, **kwargs)
  
  
  def run(self, bind=None, application=None, forks=None, handle_errors=False):
    '''Helper for running an application.
    '''
    # Make sure we have an application
    application = absapp(application)
    
    # Bind
    if bind is not None:
      os.environ['SMISK_BIND'] = bind
    if 'SMISK_BIND' in os.environ:
      smisk.core.bind(os.environ['SMISK_BIND'])
      log.info('Listening on %s', smisk.core.listening())
    
    # Enable auto-reloading if any of these are True:
    if _config.get('smisk.autoreload.modules', _config.get('smisk.autoreload.config')):
      from smisk.autoreload import Autoreloader
      ar = Autoreloader()
      ar.start()
    
    # Forks
    if isinstance(forks, int):
      application.forks = forks
    
    # Call app.run()
    if handle_errors:
      return handle_errors_wrapper(application.run)
    else:
      return application.run()
  

main = Main()


#-------------------------------------------------------------------------
# Forking utilities

def daemonize(chdir='/', umask=None, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
  '''This forks the current process into a daemon.
  The stdin, stdout, and stderr arguments are file names that
  will be opened and be used to replace the standard file descriptors
  in sys.stdin, sys.stdout, and sys.stderr.
  These arguments are optional and default to /dev/null.
  Note that stderr is opened unbuffered, so
  if it shares a file with stdout then interleaved output
  may not appear in the order that you expect.
  '''
  # Do first fork.
  try:
    pid = os.fork()
    if pid > 0:
      sys.exit(0) # Exit first parent.
  except OSError, e:
    log.critical('daemonize(): fork #1 failed: (%d) %s', e.errno, e.strerror)
    sys.exit(1)
  
  # Decouple from parent environment.
  if chdir:
    if not isinstance(chdir, basestring):
      chdir = '/'
    os.chdir(chdir)
    log.debug('changed directory to %r', chdir)
  if isinstance(umask, int):
    os.umask(umask)
    log.debug('changed umask to %d', umask)
  os.setsid()
  
  # Do second fork.
  try:
    pid = os.fork()
    if pid > 0:
      sys.exit(0) # Exit second parent.
  except OSError, e:
    log.critical('daemonize(): fork #2 failed: (%d) %s', e.errno, e.strerror)
    sys.exit(1)
  
  # Now I am a daemon
  
  # Redirect standard file descriptors.
  if stdin is None:
    stdin = '/dev/null'
  if not isinstance(stdin, file):
    stdin = file(stdin, 'r')
  
  if stdout is None:
    stdout = '/dev/null'
  if not isinstance(stdout, file):
    stdout = file(stdout, 'a+')
  
  if stderr is None:
    stderr = '/dev/null'
  if not isinstance(stderr, file):
    stderr = file(stderr, 'a+', 0)
  
  os.dup2(stdin.fileno(),  sys.stdin.fileno())
  os.dup2(stdout.fileno(), sys.stdout.fileno())
  os.dup2(stderr.fileno(), sys.stderr.fileno())


def wait_for_child_processes(options=0):
  while 1:
    try:
      pid, status = os.waitpid(-1, options)
      log.debug('process %d exited with status %d', pid, status)
    except OSError, e:
      if e.errno in (4, 10):
        # Mute "Interrupted system call" and "No child processes"
        break
      # Otherwise: delegate
      raise


def control_process_runloop(pids, signals=(signal.SIGHUP, signal.SIGINT, signal.SIGQUIT, signal.SIGTERM), cleanup=None):
  parent_sighandlers = {}
  
  def ctrl_proc_finalize(signalnum, frame):
    try:
      log.info('waiting for workers to exit cleanly')
      wait_for_child_processes()
    except KeyboardInterrupt:
      log.info('force-killing workers (SIGKILL)')
      for pid in pids:
        try:
          os.kill(pid, signal.SIGKILL)
        except OSError, e:
          # 3: No such process
          if e.errno != 3:
            raise
    # Run cleanup function
    if callable(cleanup):
      try:
        cleanup()
      except:
        log.error('cleanup function failed:', exc_info=1)
    # Call parent
    if signalnum in parent_sighandlers:
      parent_handler = parent_sighandlers[signalnum]
      if callable(parent_handler):
        log.debug('triggering parent signal handler %r', parent_handler)
        parent_handler(signalnum, frame)
  
  for signalnum in signals:
    parent_sighandlers[signalnum] = signal.signal(signalnum, ctrl_proc_finalize)
  
  try:
    wait_for_child_processes()
  except KeyboardInterrupt:
    pass
