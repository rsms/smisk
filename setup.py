#!/usr/bin/env python
# encoding: utf-8
from distutils.core import setup, Extension, Distribution, Command
from distutils import sysconfig
from distutils.sysconfig import customize_compiler
from distutils.command.build import build
from distutils.command.config import config
from distutils.command.build_ext import build_ext
from distutils.errors import DistutilsExecError
from distutils import log
from subprocess import Popen, PIPE
import os, sys, datetime
import platform

version = "1.0b"

sources = ['src/__init__.c',
           
           'src/utils.c',
           'src/atoin.c',
           'src/cstr.c',
           'src/multipart.c',
           'src/sha1.c',
           'src/file_info.c',
           'src/file_lock.c',
           'src/crash_dump.c',
           
           'src/Application.c',
           'src/Request.c',
           'src/Response.c',
           'src/Stream.c',
           'src/URL.c',
           'src/SessionStore.c',
           'src/FileSessionStore.c',
           
              'src/xml/__init__.c']

os.chdir(os.path.dirname(os.path.abspath(__file__)))
py_version = ".".join([str(s) for s in sys.version_info[0:2]]) # "M.m"

# Default. This may be overwritten later on if we are in a checkout
revision = '-'

required_libraries = [
  ('fcgi', ['fastcgi.h', 'fcgiapp.h']),
]
cflags = ''
prefix_h = 'src/prefix.h'
sys_conf_h = 'src/system_config.h'
sys_conf_py = '_config.py'
have_headers = [
  'fcntl.h',
  'sys/file.h',
  'sys/time.h',
  'sys/stat.h',
  'sys/utsname.h'
]

include_dirs = [] # created by config
library_dirs = [] # created by config
libraries = [] # created by config
X86_MACHINES = ['i386', 'i686', 'i86pc', 'amd64', 'x86_64']

#---------------------------------------

def shell_cmd(cmd):
  child_stdin = None
  child_stdout = None
  try:
    (child_stdin, child_stdout) = os.popen2(cmd)
    return child_stdout.read().strip()
  finally:
    if child_stdin: child_stdin.close()
    if child_stdout: child_stdout.close()

def revision_from_version_h():
  f = open('src/version.h', "r")
  try:
    for line in f:
      if line[:17] == '#define SMISK_REV':
        return line[24:].strip(' "\n\r\t')
  finally:
    f.close() 
  return None

def coll_wild_unique(seq):
  # Not order preserving
  return list(set(seq))

def coll_ordered_unique(seq, idfun=None):
  # Order preserving
  seen = set()
  return [x for x in seq if x not in seen and not seen.add(x)]

revision = shell_cmd("hg id -i")
repo_has_changed = not os.path.exists('src/version.h') \
  or os.path.getmtime('src/version.h') < os.path.getmtime('.hg') \
  or revision != revision_from_version_h()

# Load config if available
if os.path.isfile(sys_conf_py) and 'config' not in sys.argv:
  execfile(sys_conf_py, globals(), locals())


#---------------------------------------
# Commands

class smisk_apidocs(Command):
  description = 'Builds the documentation'
  user_options = []
  def initialize_options(self): pass
  def finalize_options(self): pass
  def run(self):
    try:
      import epydoc.markup.restructuredtext
      from epydoc import cli
      old_argv = sys.argv[1:]
      sys.argv[1:] = [
        '--config=doc/epydoc.conf',
        '--no-private', # epydoc bug, not read from config
        #'--verbose',
        '--simple-term'
      ]
      cli.cli()
      sys.argv[1:] = old_argv
    except ImportError:
      print 'epydoc not installed, skipping API documentation.'
  

class smisk_build_core(build_ext):
  description = 'Build smisk.core C extension (compile/link to build directory)'
  user_options = [
    ('debug-smisk', None, "compile Smisk with debugging information. Implies --debug"),
  ]
  def run(self):
    print 'ENTER build_ext.run'
    self._update_version_h()
    self._run_config_if_needed()
    self._configure_compiler()
    self.libraries = ['fcgi']
    build_ext.run(self)
  
  def _update_version_h(self):
    # write version.h if needed
    if not repo_has_changed:
      return
    f = open('src/version.h', "w")
    try:
      f.write("#ifndef SMISK_VERSION\n#define SMISK_VERSION \"%s\"\n#endif\n" % version)
      f.write("#ifndef SMISK_REVISION\n#define SMISK_REVISION \"%s\"\n#endif\n" % revision)
      print 'wrote version info to src/version.h'
    finally:
      f.close()
  
  def _run_config_if_needed(self):
    run_configure = True
    try:
      m = os.path.getmtime(__file__)
      if os.path.getmtime(sys_conf_h) > m or os.path.getmtime(sys_conf_py) > m:
        run_configure = False
    except os.error:
      pass
    if run_configure:
      self.run_command('config')
  
  def _configure_compiler(self):
    global cflags, include_dirs, library_dirs, libraries
    machine = platform.machine()
    
    self.define = []
    self.undef = []
    self.include_dirs = include_dirs
    self.library_dirs = library_dirs
    self.libraries = libraries
    
    cflags += ' -include %s' % prefix_h
    cflags += ' -Wall'
    
    if '--debug' in sys.argv or '--debug-smisk' in sys.argv:
      self.debug = True
      cflags += ' -O0'
      self.define.append(('DEBUG', '1'))
      if '--debug-smisk' in sys.argv:
        self.define.append(('SMISK_DEBUG', '1'))
    else:
      self.debug = False
      cflags += ' -Os'
      if machine in X86_MACHINES:
        cflags += ' -msse3'
        if platform.system() == 'Darwin':
          cflags += ' -mssse3'
    # set c flags
    if 'CFLAGS' in os.environ: os.environ['CFLAGS'] += cflags
    else: os.environ['CFLAGS'] = cflags
  

class smisk_build(build):
  description = 'will build the whole package'
  user_options = build.user_options
  user_options.append(
    ('debug-smisk', None, "compile Smisk with debugging information. Implies --debug"),
  )
  boolean_options = build.boolean_options
  boolean_options.append('debug_smisk')
  sub_commands = [('build_py',         build.has_pure_modules),
                  ('build_clib',       build.has_c_libraries),
                  ('build_core',       build.has_ext_modules),
                  ('build_scripts',    build.has_scripts),
                 ]
  
  def initialize_options(self):
    build.initialize_options(self)
    self.debug_smisk = False
  

class smisk_config(config):
  description = 'Configure build (almost like "./configure")'
  
  def initialize_options (self):
    global include_dirs, libraries
    config.initialize_options(self)
    self.noisy = 0
    self.dump_source = 0
    self.libraries = libraries
    self.include_dirs = include_dirs
  
  def run(self):
    log_threshold = log._global_log.threshold
    log._global_log.threshold = log.WARN
    self.macros = {}
    
    #self._include_dirs()
    self._machine()
    self._headers()
    self._check_libs()
    self._write_system_config_h()
    self._write_system_config_py()
    
    log._global_log.threshold = log_threshold
  
  def _include_dirs(self):
    sys.stdout.write('locating Python header search paths ... ')
    sys.stdout.flush()
    found_py = False
    for dn in [
      sys.exec_prefix + '/include/python%s' % py_version,
      sys.exec_prefix + '/include/python',
      '/opt/local/Library/Frameworks/Python.framework/Versions/%s/Headers' % py_version, # less common ports path
      '/usr/local/include/python%s' % py_version, # debian and others
      '/opt/local/include/python%s' % py_version, # bsd ports, mac ports, etc
      '/usr/include/python%s' % py_version, # debian and others
      '/usr/include/python',
      '/usr/local/include/python',
      '/opt/local/include/python',
      ]:
      if os.path.isdir(dn):
        self.include_dirs.append(dn)
        found_py = True
        break
    if not found_py:
      sys.stderr.write("\nNo Python header search paths found!\n"\
        "This is a serious error. Please contact rasmus@flajm.se.\n")
      sys.exit(1)
    else:
      print 'found:'
      self.include_dirs = coll_wild_unique(self.include_dirs)
      for s in self.include_dirs:
        print ' ', s
  
  def _machine(self):
    # Alignment
    machine = platform.machine()
    sys.stdout.write('checking machine alignment ... %s ' % machine)
    sys.stdout.flush()
    if machine in X86_MACHINES:
      sys.stdout.write("non-aligned\n")
      self.macros['SMISK_SYS_NONALIGNED'] = 1
    else:
      sys.stdout.write("aligned\n")
    
    # Endianess
    sys.stdout.write('checking machine endianess ... ')
    sys.stdout.flush()
    test = self._run('''
    int main() {
      int i = 0x11223344;
      char *p = (char *) &i;
      if (*p == 0x44) return 0;
      return 1;
    }
    ''')
    if test == 0:
      self.macros['SMISK_SYS_LITTLE_ENDIAN'] = 1
      sys.stdout.write("little\n")
    else:
      sys.stdout.write("big\n")
  
  def _headers(self):
    import re
    global have_headers
    defname_re = re.compile('[^a-zA-Z_]')
    for fn in have_headers:
      sys.stdout.write('checking for header %s ... ' % fn)
      sys.stdout.flush()
      if self.check_header(header=fn, include_dirs=include_dirs):
        sys.stdout.write("found\n")
        self.macros['HAVE_%s' % defname_re.sub('_', fn).upper()] = 1
      else:
        sys.stdout.write("missing\n")
      sys.stdout.flush()
  
  def _run(self, body, headers=None, include_dirs=None, libraries=None, library_dirs=None, lang='c'):
    self._check_compiler()
    (src, obj, prog) = self._link(body=body, headers=headers, include_dirs=include_dirs, 
                                  libraries=libraries, library_dirs=library_dirs, lang=lang)
    if prog.find('/') == -1:
      prog = './' + prog
    ps = Popen(shell=True, args=[prog])
    exit_code = ps.wait()
    self._clean()
    return exit_code
  
  def _check_libs(self):
    global required_libraries, libraries
    for n in required_libraries:
      sys.stdout.write('checking for library %s ... ' % n[0])
      sys.stdout.flush()
      if not self.check_lib(library=n[0], headers=n[1]):
        sys.stdout.write("missing\n")
        sys.stderr.write("Error: missing library '%s'" % n[0])
        if n[1]:
          sys.stderr.write(" or one of the required headers is missing:\n")
          for h in n[1]:
            sys.stderr.write("  %s\n" % h)
        else:
          sys.stdout.write("\n")
        sys.exit(1)
      else:
        sys.stdout.write("found\n")
        self.libraries.append(n[0])
  
  def _write_system_config_h(self):
    import re
    f = open(sys_conf_h, "w")
    try:
      try:
        f.write("/* Generated by setup.py at %s */\n" % datetime.datetime.now())
        f.write("#ifndef SMISK_SYSTEM_CONFIG_H\n")
        f.write("#define SMISK_SYSTEM_CONFIG_H\n\n")
        for k,v in self.macros.iteritems():
          f.write("#ifndef %s\n" % k)
          f.write(" #define %s %s\n" % (k, str(v)) )
          f.write("#endif\n")
        f.write("\n#endif\n")
        print 'wrote compile-time configuration to %s' % sys_conf_h
      finally:
        f.close()
    except:
      os.remove(sys_conf_h)
      raise
  
  def _write_system_config_py(self):
    import re
    f = open(sys_conf_py, "w")
    try:
      try:
        f.write("# encoding: utf-8\n")
        f.write("# Generated by setup.py at %s\n" % datetime.datetime.now())
        f.write("include_dirs = %s\n" % repr(coll_wild_unique(include_dirs)))
        f.write("library_dirs = %s\n" % repr(coll_wild_unique(library_dirs)))
        f.write("libraries = %s\n" % repr(coll_wild_unique(libraries)))
        f.write("\n")
        print 'wrote distutils configuration to %s' % sys_conf_py
      finally:
        f.close()
    except:
      os.remove(sys_conf_py)
      raise
  


class SmiskDistribution(Distribution):
  def __init__(self,attrs=None):
    Distribution.__init__(self, attrs)
    self.cmdclass = {
      'build': smisk_build,
        'build_core': smisk_build_core,
      'apidocs': smisk_apidocs,
      'config': smisk_config
    }

# ugly fix because unixcompiler seem to be "broken"
_undef_macros=[]
if '--debug' in sys.argv or '--debug-smisk' in sys.argv:
  _undef_macros=['NDEBUG']

#build.user_options.append(('debug-smisk', None, "compile Smisk with debugging information. Implies --debug"))

#---------------------------------------
setup (
  distclass=SmiskDistribution,
  name = 'smisk',
  version = version + '-' + revision,
  description = "High-performance web service framework",
  long_description = """
Smisk is a simple, high-performance and scalable web service framework
written in C, but controlled by Python.

It is designed to widen the common bottle necks common in heavy-duty web
services.

The latest development version is available in
<a href="http://svn.hunch.se/smisk/trunk">the Smisk subversion repository</a>.
""",
  url = 'http://trac.hunch.se/smisk',
  download_url = 'http://trac.hunch.se/smisk/wiki/Download',
  author = 'Rasmus Andersson',
  author_email = 'rasmus@flajm.se',
  license = 'MIT',
  classifiers = [
    'Development Status :: 4 - Beta',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: MacOS :: MacOS X',
    'Operating System :: POSIX :: Linux',
    'Operating System :: Unix',
    'Programming Language :: C',
    'Programming Language :: Python',
    'Topic :: Internet :: WWW/HTTP',
    'Topic :: Software Development :: Libraries :: Python Modules'],
  package_dir = {'': 'lib'},
  packages = ['smisk'],
  ext_modules = [Extension(
    name='smisk.core',
    sources=sources,
    undef_macros=_undef_macros
  )]
)
