# encoding: utf-8
'''Tests using a live host server, testing http transactions, etc.
'''
import sys, os, logging, time, unittest
import threading, select, httplib
from subprocess import Popen, PIPE
from smisk.test import TestCase

log = logging.getLogger(__name__)

# This might be adjusted (by code at end of this module)
functional = True
'''Indicates if the current system is able to runt the tests in
this module or not.
'''

class LighttpdReconstructedError(Exception):
  pass

class FCGIBackendFailedToStartError(LighttpdReconstructedError):
  pass


def sh(cmd):
  '''Execute command in shell, returning value of stdout.
  Raises OSError if cmd is not found or exists with status != 0
  '''
  ps = Popen(cmd, stdout=PIPE, stderr=PIPE, close_fds=True, shell=True)
  subprocess_pipes = ps.communicate()
  status = ps.wait()
  if status != 0:
    raise OSError('%r exited with status %d: %s' % (cmd, status, subprocess_pipes[1].strip()))
  return subprocess_pipes[0].strip()

  
def relpath2abs(path, relative_to_dir):
  if path and path[0] == '/':
    return path
  return os.path.abspath(os.path.join(relative_to_dir, path))


def _class_logger(obj):
  return logging.getLogger(obj.__class__.__module__+'.'+obj.__class__.__name__)


def _instance_logger(obj):
  return logging.getLogger('%s.%s@0x%x' % (obj.__class__.__module__, obj.__class__.__name__, id(obj)))


# Upate Popen
if not hasattr(Popen, 'terminate'):
  def Popen_send_signal(self, sig):
    os.kill(self.pid, sig)
  Popen.send_signal = Popen_send_signal
  def Popen_terminate(self):
    self.send_signal(15)
  Popen.terminate = Popen_terminate
  def Popen_kill(self):
    self.send_signal(9)
  Popen.kill = Popen_kill


class ProcessIOSupervisor(threading.Thread):
  def __init__(self, p, delegate):
    super(ProcessIOSupervisor, self).__init__()
    self.log = _class_logger(self)
    self.p = p
    self.delegate = delegate
    self.finished = threading.Event()
  
  
  def run(self):
    read_set = []
    stdout = None
    stderr = None
    
    if self.p.stdout:
      read_set.append(self.p.stdout)
      stdout = []
    if self.p.stderr:
      read_set.append(self.p.stderr)
      stderr = []
    
    self.log.debug('watching %d read-FDs for process %d',
                   len(read_set), self.p.pid)
    
    try:
      while not self.finished.isSet() and read_set:
        rlist, wlist, xlist = select.select(read_set, [], [])
        
        if self.p.stdout in rlist:
          line = os.read(self.p.stdout.fileno(), 4096)
          if line:
            self.delegate.on_process_stdout(self.p, line)
          else:
            read_set.remove(self.p.stdout)
        
        if self.p.stderr in rlist:
          line = os.read(self.p.stderr.fileno(), 4096)
          if line:
            self.delegate.on_process_stderr(self.p, line)
          else:
            read_set.remove(self.p.stderr)
        
        if self.p.stderr not in rlist and self.p.stdout not in rlist:
          self.log.info('neither stderr nor stdout left in rlist -- stopping')
          break
    except Exception, e:
      self.delegate.on_process_exception(*sys.exc_info())
      self.stop()
    
    self.stop()
  
  
  def stop(self):
    if not self.finished.isSet():
      self.finished.set()
      self.log.debug('stopped')
  
  
  def __del__(self):
    self.stop()
  


class LighttpdServer(object):
  binary = ''
  '''Path to lighttpd binary
  '''
  
  features = []
  '''Lighttpd features (all things with a "+" listed in "lighttpd -V")
  '''
  
  version = (0,0,0)
  '''Lighttpd version
  '''
  
  working_dir = None
  '''If not set, the working directory is deduced from 
  dirname(self.config) upon calling start()
  '''
  
  def __init__(self, config='lighttpd.conf', basedir=None):
    if not basedir:
      basedir = os.path.dirname(sys.modules[self.__class__.__module__].__file__)
    self.log = _class_logger(self)
    self.p = None
    self.io_supervisor = None
    self.config = relpath2abs(config, basedir)
    self.port = int(sh("lighttpd -pf '%s' | grep server.port" % self.config).rsplit(' ',1)[1])
    self.ready = False
  
  
  @property
  def running(self):
    if self.p:
      return True
    return False
  
  
  def on_process_stdout(self, p, output):
    self.log.debug('STDOUT: %r', output)
  
  
  def on_process_stderr(self, p, output):
    self.log.debug('STDERR: %r', output)
    
    if not self.ready and 'server started' in output:
      self.ready = True
      self.on_server_ready(self)
    elif "can't bind to port" in output:
      if 'Address already in use' in output:
        raise RuntimeError('Address already in use')
      else:
        raise RuntimeError(output.split(') ',1)[1])
    elif 'the fastcgi-backend' in output and 'failed to start' in output:
      s = output[output.index('the fastcgi-backend ')+20:]
      s = s[:s.index(' ')]
      raise FCGIBackendFailedToStartError(s)
  
  
  def on_process_exception(self, typ, e, tb):
    self.log.error('Server failed:', exc_info=(typ, e, tb))
    self.stop()
  
  
  # Callback
  def on_server_ready(self, server):
    pass
  
  
  # Callback
  def on_server_stopped(self, server):
    pass
  
  
  def start(self, timeout=10.0):
    if self.p:
      raise Exception('server is already running')
    cmd = [self.binary, '-D', '-f', self.config]
    cwd = self.working_dir
    if not cwd:
      cwd = os.path.dirname(os.path.abspath(self.config))
    self.log.debug('starting: %s', ' '.join(cmd))
    self.log.debug('working directory: %s', cwd)
    self.p = Popen(cmd, stderr=PIPE, stdout=PIPE, close_fds=True, cwd=cwd)
    self.io_supervisor = ProcessIOSupervisor(self.p, self)
    self.io_supervisor.start()
    
    if not self.ready  and  timeout is not None  and  timeout > 0.0:
      start_ev = threading.Event()
      orig_on_server_ready = self.on_server_ready
      def on_ready_proxy(server):
        start_ev.set()
      if not self.ready:
        self.on_server_ready = on_ready_proxy
        try:
          start_ev.wait(timeout)
          if not start_ev.isSet()  and  not self.ready:
            raise RuntimeError('server failed to start -- timeout reached (%f sec)' % timeout)
        finally:
          self.on_server_ready = orig_on_server_ready
  
  
  def stop(self, gracetime=10.0):
    if not self.io_supervisor and not self.p:
      return
    
    self.log.debug('stopping server')
    
    if self.io_supervisor:
      self.io_supervisor.stop()
      self.io_supervisor = None
    
    if self.p:
      self.log.debug('sending SIGTERM to %r [%d]', self.p, self.p.pid)
      self.p.terminate()
      pid = self.p.poll()
      if pid is not None:
        self.log.debug('waiting for %s [%d] to exit', self.binary, pid)
        time_start_wait = time.time()
        while 1:
          if self.p.poll() is not None:
            break
          if time.time()-time_start_wait > gracetime:
            self.log.debug('sending SIGTERM to %r [%d]', self.p, self.p.pid)
            self.p.terminate()
            time.sleep(0.1)
            if self.p.poll() is None:
              self.log.debug('sending SIGKILL to %r [%d]', self.p, self.p.pid)
              self.p.kill()
            break
          time.sleep(0.1)
      os.waitpid(self.p.pid, 0)
      self.log.debug('process %r [%d] exited', self.p, self.p.pid)
      self.p = None
      self.on_server_stopped(self)
  
  
  def __del__(self):
    self.stop()
  
  
  @classmethod
  def setup(cls):
    # Find binary
    cls.binary = sh('which lighttpd')
    if not cls.binary:
      global functional
      functional = False
      return
    
    # Parse version
    cls.version = tuple([int(s) for s in sh(cls.binary + ' -v').split(' ',1)[0].split('-')[1].split('.')])
    
    # Parse features
    cls.features = []
    for line in sh(cls.binary + ' -V').split('\n'):
      line = line.strip()
      if line.startswith('+'):
        cls.features.append(line.split(' ')[1])
  

class HTTPResponse(httplib.HTTPResponse):
  _body = None
  
  @property
  def status_line(self):
    # i.e. "HTTP/1.1 200 OK"
    return '%s %s %s' % (self.version_name, self.status, self.reason)
  
  @property
  def version_name(self):
    return {10:'HTTP/1.0',11:'HTTP/1.1'}[self.version]
  
  @property
  def is_server_error(self):
    return self.status % 500 < 100
  
  @property
  def is_client_error(self):
    return self.status % 400 < 100
  
  @property
  def is_ok(self):
    return self.status % 200 < 100
  
  @property
  def headers(self):
    for kv in self.getheaders():
      yield kv
  
  def header(self, header_named):
    header_named = header_named.lower()
    for k,v in self.headers:
      if k == header_named:
        yield v
  
  def get_header(self, header_named, default=None):
    header_named = header_named.lower()
    for k,v in self.headers:
      if k == header_named:
        return v
    return default
  
  def headerEquals(self, header_named, eq_string):
    header_named = header_named.lower()
    for k,v in self.headers:
      if k == header_named:
        if v == eq_string:
          return True
        else:
          break
    return False
  
  def headerIsSet(self, header_named):
    header_named = header_named.lower()
    for k,v in self.headers:
      if k == header_named:
        return True
    return False
  
  @property
  def body(self):
    if self._body is None:
      self._body = self.read()
    return self._body
  
  def dump(self, stream=sys.stdout):
    '''Dump the full response.
    '''
    print >> stream, {10:'HTTP/1.0',11:'HTTP/1.1'}[self.version], self.status, self.reason
    for kv in self.getheaders():
      print >> stream, '%s: %s' % kv
    print >> stream, ''
    print >> stream, self.read()
  


class Client(object):
  '''Simple HTTP client
  '''
  host = '127.0.0.1'
  
  def __init__(self, server):
    self.server = server
    self.conn = None
    self._conn_debug_level = 0
  
  def connect(self, ssl=False):
    if ssl:
      self.conn = httplib.HTTPSConnection(self.host, self.server.port)
    else:
      self.conn = httplib.HTTPConnection(self.host, self.server.port)
    self.conn.response_class = HTTPResponse
    self.conn.set_debuglevel(self._conn_debug_level)
    self.conn.connect()
  
  def reconnect(self, ssl=None):
    if ssl is None:
      ssl = isinstance(self.conn, httplib.HTTPSConnection)
    self.disconnect()
    self.connect(ssl=ssl)
  
  def disconnect(self):
    if self.conn:
      try:
        self.conn.close()
        self.conn = None
      except:
        pass
  
  def get_debug(self):
    return self._conn_debug_level
  
  def set_debug(self, level):
    if self.conn:
      self.conn.set_debuglevel(level)
    self._conn_debug_level = level
  
  debug = property(get_debug, set_debug)
  
  def request(self, method, uri, body=None, headers=None):
    if not self.conn:
      raise Exception('Not connected')
    try:
      skip_host = False
      
      if headers:
        for header in headers:
          if header[0].lower() == 'host':
            skip_host = True
      
      self.conn.putrequest(method, uri, skip_host=skip_host, skip_accept_encoding=True)
      
      if headers:
        for header in headers:
          self.conn.putheader(header[0], *header[1:])
      
      self.conn.endheaders()
      
      if body:
        if hasattr(body, 'read'):
          while 1:
            s = body.read(1024)
            if not s:
              break
            self.conn.send(s)
        else:
          self.conn.send(body)
      
      return self.conn.getresponse()
    except:
      if self.conn:
        self.conn.close()
      raise
  
  def __del__(self):
    self.disconnect()
  


class LiveTestCase(TestCase):
  def setUp(self, basedir=None):
    if not basedir:
      basedir = os.path.dirname(sys.modules[self.__class__.__module__].__file__)
    logging.basicConfig(level=logging.WARN, format="%(name)-40s %(message)s")
    self.server = LighttpdServer(basedir=basedir)
    self.server.start()
    self._connections = []
  
  def connection(self):
    client = Client(self.server)
    client.connect()
    self._connections.append(client)
    return client
  
  def tearDown(self):
    for client in self._connections:
      try:
        client.disconnect()
      except:
        pass
    try:
      self.server.stop()
      while 1:
        pid, status, rusage = os.wait3(os.WNOHANG)
        if pid == 0:
          break
        #print 'killing %d' % pid 
        os.kill(pid, 9)
    except:
      pass
  
  def __del__(self):
    self.tearDown()
  
  def assertResponseHeaderEquals(self, rsp, header_named, eq_string):
    if not rsp.headerEquals(header_named, eq_string):
      v = rsp.get_header(header_named)
      raise AssertionError("value of response header %r: %r != %r" %\
        (header_named, v, eq_string))
  
  def assertResponseHeaderIsSet(self, rsp, header_named):
    if not rsp.headerIsSet(header_named):
      raise AssertionError("response header %r is not set" % header_named)
  
  def assertResponseHeaderNotSet(self, rsp, header_named):
    if rsp.headerIsSet(header_named):
      raise AssertionError("response header %r is set" % header_named)
  


# Test system, version, etc
LighttpdServer.setup()


def suite_if_possible(*tests):
  v = []
  if functional:
    v = [unittest.makeSuite(test) for test in tests]
  else:
    print 'Notice: live tests disabled (see module smisk.test.live for more info)'
  return unittest.TestSuite(v)


if __name__ == '__main__':
  if not functional:
    print >> sys.stderr, 'System incompatible with this module. '\
      'Maybe LigHTTPd is not installed?'
    sys.exit(1)
  
  logging.basicConfig(level=logging.DEBUG, format="%(name)-30s %(levelname)-8s %(message)s")
  
  server = LighttpdServer()
  try:
    server.start()
    
    cli = Client(server)
    cli.connect()
    r = cli.request('GET', '/')
    r.dump()
    
  finally:
    server.stop()

