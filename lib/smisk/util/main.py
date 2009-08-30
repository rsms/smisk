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
	                  metavar="<path>",
	                  default=appdir)
	
	parser.add_option("-b", "--bind",
	                  dest="bind",
	                  help='Start a stand-alone process, listening for FastCGI connection on '\
	                       '<addr>, which can be a TCP/IP address with out without host or a UNIX '\
	                       'socket (named pipe on Windows). For example "localhost:5000", '\
	                       '"/tmp/my_process.sock" or ":5000".%s' % bind_defaults_to,
	                  metavar="<addr>",
	                  action="store",
	                  type="string",
	                  default=bind)
	
	parser.add_option("-c", "--forks",
	                  dest="forks",
	                  help='Set number of childs to fork.%s' % forks_defaults_to,
	                  metavar="<count>",
	                  type="int",
	                  default=forks)
	
	parser.add_option("-s", "--spawn",
	                  dest="spawn",
	                  help='Spawn <count> number of instances based on --bind. If --bind specifies '\
	                       'a TCP address, each instance will increase the port number. If --bind '\
	                       'is a UNIX socket, a incremental number is added as a suffix to the '\
	                       'sockets filename.',
	                  metavar="<count>",
	                  type="int",
	                  default=0)
	
	parser.add_option("", "--chdir",
	                  dest="chdir",
	                  help='Change directory to <path> before starting application.',
	                  metavar="<path>",
	                  type="string",
	                  default=None)
	
	parser.add_option("", "--umask",
	                  dest="umask",
	                  help='Change umask to <mask> before starting application.',
	                  metavar="<mask>",
	                  type="int",
	                  default=None)
	
	parser.add_option("", "--stdout",
	                  dest="stdout",
	                  help='Redirect stdout to <path> before spawning application. Recommended: /dev/null',
	                  metavar="<path>",
	                  type="string",
	                  default=None)
	
	parser.add_option("", "--stderr",
	                  dest="stderr",
	                  help='Redirect stderr to <path> before spawning application. Recommended: /dev/null',
	                  metavar="<path>",
	                  type="string",
	                  default=None)
	
	parser.add_option("", "--pidfile",
	                  dest="pidfile",
	                  help='Write process identifier to <path>. Multiple PIDs are separated by LF.',
	                  metavar="<path>",
	                  type="string",
	                  default=None)
	
	parser.add_option("", "--debug",
	                  dest="debug",
	                  help="sets log level to DEBUG",
	                  action="store_true",
	                  default=False)
	
	parser.add_option("-H", "--http",
	                  dest="http_",
	                  help='Run this application through a built-in HTTP server. Shorthand for --http-port 8080.',
	                  action="store_true",
	                  default=False)
	
	parser.add_option("", "--http-port",
	                  dest="http_port",
	                  help='Run this application through a built-in HTTP server listening on port <port>.',
	                  metavar="<port>",
	                  type="int",
	                  default=0)
	
	parser.add_option("", "--http-addr",
	                  dest="http_addr",
	                  help='Run this application through a built-in HTTP server bound to <host>.',
	                  metavar="<host>",
	                  type="string",
	                  default='localhost')
	
	opts, args = parser.parse_args()
	
	# Make sure empty values are None
	if opts.debug:
		_config.loads("'logging': {'levels':{'':'DEBUG'}}")
	if not opts.bind:
		opts.bind = None
	if not opts.appdir:
		opts.appdir = None
	if not opts.forks:
		opts.forks = None
	
	if opts.http_:
		opts.http_port = 8080
	
	return opts.appdir, opts.bind, opts.forks, opts.spawn, opts.chdir, \
	       opts.umask, opts.stdout, opts.stderr, opts.pidfile, opts.http_port


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
	
	:param	error_cb:	 Called after an exception was caught and info 
	                   has been written to ``error.log``. Receives a
	                   single argument: Status code as an integer.
	                   Defaults to ``sys.exit`` causing normal program
	                   termination. The returned value of this callable
	                   will be returned by `handle_errors_wrapper` itself.
	:type	 error_cb:	 callable
	:param	abort_cb:	 Like `error_cb` but instead called when
											``KeyboardInterrupt`` was raised.
	:type	 abort_cb:	 callable
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
			logfile = os.environ.get('SMISK_LOG_DIR', os.environ.get(os.environ['SMISK_APP_DIR'], '.'))
			logfile = os.path.join(logfile, 'error.log')
			logfile = os.path.abspath(_config.get('smisk.emergency_logfile', logfile))
			f = open(logfile, 'a')
			try:
				from traceback import print_exc
				from datetime import datetime
				f.write(datetime.now().isoformat())
				f.write(" [%d] " % os.getpid())
				print_exc(1000, f)
			finally:
				f.close()
				try:
					print_exc(1000, sys.stderr)
				except:
					pass
				sys.stderr.write('Wrote emergency log to %s\n' % logfile)
		except Exception, e:
			try:
				sys.stderr.write('Failed to write emergency log to %s: %s\n' % (logfile, e))
			except:
				pass
		# Call error callback
		if error_cb:
			return error_cb(1)


class Main(object):
	default_app_type = smisk.core.Application
	_is_set_up = False
	pidfile = None
	
	def __call__(self, application=None, appdir=None, bind=None, forks=None, 
	             handle_errors=True, cli=True, config=None, pidfile=None, 
	             chdir=None, umask=None, spawn=None,
	             *args, **kwargs):
		'''Helper for setting up and running an application.
		
		If several servers are spawned a list of PIDs is returned, otherwise
		whatever returned by application.run() is returned.
		'''
		stdout = stderr = http_addr = None
		http_port = 0
		if cli:
			appdir, bind, forks, spawn, chdir, umask, stdout, stderr, pidfile, http_port \
			 = main_cli_filter(appdir=appdir, bind=bind, forks=forks)
		
		# Setup
		if handle_errors:
			application = handle_errors_wrapper(self.setup, application=application, 
			                                    appdir=appdir, config=config, *args, **kwargs)
		else:
			application = self.setup(application=application, appdir=appdir, config=config, *args, **kwargs)
		
		# Pidfile?
		if pidfile:
			self.pidfile = pidfile
			try:
				open(self.pidfile, 'w').close()
			except:
				pass
		
		# Run method kewyords
		run_kwargs = dict(bind=bind, application=application, forks=forks, handle_errors=handle_errors)
		
		# Spawn?
		if spawn:
			def childfunc(childno, bindarg):
				_chdir = chdir # ref workaround
				print 'server %d starting at %s' % (os.getpid(), bindarg)
				if _chdir is None:
					_chdir = '/'
				daemonize(chdir, umask, '/dev/null', stdout, stderr)
				run_kwargs['bind'] = bindarg
				self.run(**run_kwargs)
			socket, startport, address, args = parse_bind_arg(bind)
			childs = fork_binds(spawn, childfunc, socket=socket, startport=startport, address=address)
			return childs
		else:
			_prepare_env(chdir=chdir, umask=umask)
			if http_port:
				# fork off the app
				run_kwargs['bind'] = '127.0.0.1:5000'
				app_pid = self.run_deferred(**run_kwargs)
				# start the http server
				from smisk.util.httpd import Server
				if not http_addr:
					http_addr = 'localhost'
				server = Server((http_addr, http_port))
				orig_sighandlers = {}
				
				def kill_app_sighandler(signum, frame):
					try:
						print 'sending SIGKILL to application %d...' % app_pid
						log.debug('sending SIGKILL to application %d...', app_pid)
						os.kill(app_pid, 9)
					except:
						pass
				
				def sighandler(signum, frame):
					try:
						print 'sending signal %d to application %d...' % ( signum, app_pid)
						log.debug('sending signal %d to application %d...', signum, app_pid)
						os.kill(app_pid, signum)
					except:
						pass
					try:
						orig_alarm_handler = signal.signal(signal.SIGALRM, kill_app_sighandler)
						signal.alarm(2) # 2 sec delay until SIGKILLing
						os.waitpid(-1, 0)
						signal.alarm(0) # cancel SIGKILL
						signal.signal(signal.SIGALRM, orig_alarm_handler)
					except:
						pass
					try:
						orig_sighandlers[signum](signum, frame)
					except:
						pass
					signal.signal(signal.SIGALRM, lambda x,y: os._exit(0))
					signal.alarm(2) # 2 sec time limit for cleanup functions
					sys.exit(0)
				
				logging.basicConfig(level=logging.DEBUG)
				orig_sighandlers[signal.SIGINT] = signal.signal(signal.SIGINT, sighandler)
				orig_sighandlers[signal.SIGTERM] = signal.signal(signal.SIGTERM, sighandler)
				orig_sighandlers[signal.SIGHUP] = signal.signal(signal.SIGHUP, sighandler)
				print 'httpd listening on %s:%d' % (http_addr, http_port)
				server.serve_forever()
				os.kill(os.getpid(), 2)
				os.kill(os.getpid(), 15)
			else:
				# Run
				return self.run(**run_kwargs)
	
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
	
	
	
	def run_deferred(self, signal_parent_after_exit=signal.SIGTERM, keepalive=True, *va, **kw):
		pid = _fork()
		if pid == -1:
			log.error('fork() failed')
		if pid == 0:
			try:
				while True:
					print 'starting app'
					self.run(*va, **kw)
					if not keepalive:
						break
				try:
					if signal_parent_after_exit:
						os.kill(os.getppid(), signal_parent_after_exit)
				except:
					pass
			finally:
				os._exit(0)
		else:
			return pid
	
	def run(self, bind=None, application=None, forks=None, handle_errors=False):
		'''Helper for running an application.
		'''
		# Write PID
		if self.pidfile:
			flags = os.O_WRONLY | os.O_APPEND
			if hasattr(os, 'O_EXLOCK'):
				flags = flags | os.O_EXLOCK
			fd = os.open(self.pidfile, flags)
			try:
				os.write(fd, '%d\n' % os.getpid())
			finally:
				os.close(fd)
		
		# Make sure we have an application
		application = absapp(application)
		
		# Bind
		if bind is not None:
			os.environ['SMISK_BIND'] = bind
		if 'SMISK_BIND' in os.environ:
			smisk.core.bind(os.environ['SMISK_BIND'])
			log.info('Listening on %s', smisk.core.listening())
		
		# Enable auto-reloading if any of these are True:
		if _config.get('smisk.autoreload.modules') \
		or _config.get('smisk.autoreload.config', _config.get('smisk.autoreload')):
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

def _prepare_env(chdir=None, umask=None):
	if isinstance(chdir, basestring):
		os.chdir(chdir)
		log.debug('changed directory to %r', chdir)
	if isinstance(umask, int):
		os.umask(umask)
		log.debug('changed umask to %d', umask)

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
			os._exit(0) # Exit parent without calling cleanup handlers, flushing stdio buffers, etc.
	except OSError, e:
		log.critical('daemonize(): fork #1 failed: (%d) %s', e.errno, e.strerror)
		sys.exit(1)
	
	# Decouple from parent environment.
	_prepare_env(chdir, umask)
	os.setsid()
	
	# Do second fork.
	try:
		pid = os.fork()
		if pid > 0:
			os._exit(0) # Exit second parent.
	except OSError, e:
		log.critical('daemonize(): fork #2 failed: (%d) %s', e.errno, e.strerror)
		sys.exit(1)
	
	# Now I am a daemon
	
	# Redirect standard file descriptors.
	if stdin:
		if not isinstance(stdin, file):
			stdin = file(stdin, 'r')
		os.dup2(stdin.fileno(),	sys.stdin.fileno())
	
	if stdout:
		if not isinstance(stdout, file):
			stdout = file(stdout, 'a+')
		os.dup2(stdout.fileno(), sys.stdout.fileno())
	
	if stderr:
		if not isinstance(stderr, file):
			stderr = file(stderr, 'a+', 0)
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


def control_process_runloop(pids, signals=(signal.SIGINT, signal.SIGQUIT, signal.SIGTERM), cleanup=None):
	def signal_children(signum):
		for pid in pids:
			try:
				os.kill(pid, signum)
			except OSError, e:
				# 3: No such process
				if e.errno != 3:
					raise
	
	def ctrl_proc_finalize(signum, frame):
		try:
			signal_children(signum)
			wait_for_child_processes()
		except:
			signal_children(signal.SIGKILL)
		if cleanup and callable(cleanup):
			try:
				cleanup(signum, frame)
			except:
				log.error('cleanup function failed:', exc_info=1)
	
	for signum in signals:
		signal.signal(signum, ctrl_proc_finalize)
	
	wait_for_child_processes()


def find_program_path(file, env=None, default=None, check_access=os.X_OK):
	if env is None:
		env = os.environ
	
	head, tail = os.path.split(file)
	if head and os.access(file, check_access):
		return file
	if 'PATH' in env:
		envpath = env['PATH']
	else:
		envpath = os.path.defpath
	PATH = envpath.split(os.path.pathsep)
	saved_exc = None
	saved_tb = None
	for dir in PATH:
		path = os.path.join(dir, file)
		if os.access(path, check_access):
			return path
	return default



def parse_bind_arg(args):
	'''Parse --bind argument into tuple (str socket, int port, str address, list argswithoutbind)
	'''
	socket = port = address = None
	nargs = []
	bargs = []
	
	if isinstance(args, basestring):
		bargs.append(args)
	elif args != None:
		n = False
		for arg in args:
			if n == True and arg and arg[0] != '-':
				bargs.append(arg)
				n = False
			elif arg == '--bind' or arg == '-b':
				n = True
			else:
				nargs.append(arg)
	
	if bargs:
		dst = bargs[0]
		if dst[0] == ':':
			port = int(dst[1:])
		elif ':' in dst:
			p = dst.index(':')
			port = int(dst[p+1:])
			address = dst[:p]
		else:
			socket = dst
	
	return (socket, port, address, nargs)

def extrapolate_binds(count, socket=None, port=5000, address=None):
	args = []
	if socket:
		if '%d' not in socket:
			socket += '%d'
		for n in range(count):
			args.append(socket % n)
	else:
		if not address:
			address = '127.0.0.1'
		if not port:
			port = 5000
		else:
			port = int(port)
		for n in range(count):
			args.append('%s:%s' % (address, port + n))
	return args

def _fork():
	sys.stdout.flush()
	sys.stderr.flush()
	try:
		os.fsync(sys.stdout.fileno())
		os.fsync(sys.stderr.fileno())
	except:
		pass
	return os.fork()

def fork_binds(count, childfunc, socket=None, startport=None, address=None, include_calling_thread=False):
	'''Spawn <count> number of forked <childfunc>s and return list of PIDs.
	
	Childfunc prototype:
	
		def childfunc(int childno, str bindarg):
			pass
	
	'''
	childs = []
	if not callable(childfunc):
		raise ValueError('childfunc must be a callable')
	
	binds = extrapolate_binds(count, socket, startport, address)
	
	for i in range(count):
		if include_calling_thread and i == count-1:
			log.info('child spawned successfully. PID: %d' % os.getpid())
			childs.append(os.getpid())
			childfunc(i, binds[i])
			return childs
		
		pid = _fork()
		if pid == -1:
			log.error('fork() failed')
			break
		if pid == 0:
			childfunc(i, binds[i])
			os._exit(0)
		else:
			log.info('child spawned successfully. PID: %d' % pid)
			childs.append(pid)
	
	return childs
	
