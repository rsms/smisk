# encoding: utf-8
'''Program main routine helpers.
'''
import sys, os, logging

__all__ = ['main']
log = logging.getLogger(__name__)

BIND_ADDR = '%s:%s'
BIND_SOCKET = '%s%s'


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


def main():
  '''Spawn processes
  '''
  from optparse import OptionParser
  parser = OptionParser(usage='usage: %prog [options] program [fcgiapp options]\n'\
    'Spawn and control processes.')
  parser.allow_interspersed_args = False
  parser.add_option("-c", "--count",
                    dest="count",
                    help='number of programs to start. Default is 5.',
                    metavar="COUNT",
                    action="store",
                    type="int",
                    default=5)
  parser.add_option("-p", "--startport",
                    dest="startport",
                    help='first port number to start binding to. Defaults to 5000.',
                    metavar="PORT",
                    action="store",
                    type="int",
                    default=5000)
  parser.add_option("-s", "--socket",
                    dest="socket",
                    help='UNIX socket to bind to. Suffixed with an increasing number '\
                      'for each process started.',
                    metavar="PATH",
                    type="string")
  parser.add_option("-a", "--address",
                    dest="address",
                    help='Address to bind to. Defaults to 127.0.0.1 if --port is set and is '\
                      'unconditionally ignored when --socket is set.',
                    metavar="ADDR",
                    type="string",
                    default='127.0.0.1')
  
  opts, args = parser.parse_args()
  print 'opts:', opts
  print 'args:', args
  
  if len(args) == 0:
    parser.error('missing program argument')
  
  for arg in args:
    if arg == '--bind' or arg == '-b':
      parser.error('--bind (or -b) can not be specified for program')
  
  program = find_program_path(args[0])
  if program is None:
    program = args[0]
    if not os.access(program, os.F_OK):
      parser.error('program %r does not exist' % program)
    if not os.access(program, os.R_OK):
      parser.error('program %r is not readable' % program)
    if not os.access(program, os.X_OK):
      parser.error('program %r is not executable' % program)
    parser.error('program %r can not be used (unknown problem)' % program)
  
  args.append('--bind')
  args.append('<replaced in fork loop>')
  bind_val = BIND_ADDR
  if opts.socket != None:
    bind_val = BIND_SOCKET 
  
  childs = []
  port = opts.startport-1
  
  for i in range(opts.count):
    if bind_val is BIND_ADDR:
      args[-1] = BIND_ADDR % (opts.address, opts.startport + i)
    else:
      if i == 0:
        args[-1] = BIND_SOCKET % (opts.socket, '127.0.0.1')
      else:
        args[-1] = BIND_SOCKET % (opts.socket, '-%d' % i)
    sys.stdout.flush()
    sys.stderr.flush()
    try:
      os.fsync(sys.stdout.fileno())
      os.fsync(sys.stderr.fileno())
    except:
      pass
    print 'pid = os.fork()'
    #pid = os.fork()
    print 'os.execve(%r, %r, os.environ)' % (program, args)
    #os.execve(path, args, os.environ)
  

main()