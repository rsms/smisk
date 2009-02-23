#!/usr/bin/env python
# encoding: utf-8
try:
  from setuptools import setup
except ImportError:
  from ez_setup import use_setuptools
  use_setuptools()
  from setuptools import setup

import sys, os, time, platform, re, subprocess

from setuptools import Extension as _Extension, Distribution, Command
from pkg_resources import parse_version
from distutils import log
from subprocess import Popen, PIPE
from ConfigParser import SafeConfigParser as ConfigParser

if sys.version_info < (2, 4):
  raise SystemExit("Python 2.4 or later is required")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
execfile(os.path.join("lib", "smisk", "release.py"))
# Load config
cfg = ConfigParser()
cfg.read('setup.cfg')
tag = ''
v = None
release_version = version
if cfg.has_option('egg_info', 'tag_build'):
  tag = cfg.get('egg_info', 'tag_build')
  release_version = release_version + tag.strip()
  v = parse_version(release_version)
else:
  v = parse_version(version)

if '--release-version' in sys.argv:
  print release_version
  sys.exit(0)

# we just need to do this right here. sorry.
undef_macros=[]
if '--debug' in sys.argv or '--debug-smisk' in sys.argv:
  undef_macros=['NDEBUG']

SYS_CONF_H = os.path.join(BASE_DIR, "src", "system_config.h")
X86_MACHINES = ['i386', 'i686', 'i86pc', 'amd64', 'x86_64']
HAVE_HEADERS = [
  'fcntl.h',
  'sys/file.h',
  'sys/time.h',
  'sys/stat.h',
  'sys/utsname.h'
]

#-------------------------------

sources = [
  'src/__init__.c',
   
  'src/utils.c',
  'src/uid.c',
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

    'src/xml/__init__.c',
    'src/bsddb.c']


classifiers = [
  'Environment :: Console',
  'Intended Audience :: Developers',
  'Intended Audience :: Information Technology',
  'License :: OSI Approved :: MIT License',
  'Operating System :: MacOS :: MacOS X',
  'Operating System :: POSIX',
  'Operating System :: Unix',
  'Programming Language :: C',
  'Programming Language :: Python',
  'Natural Language :: English',
  'Topic :: Internet :: WWW/HTTP',
  'Topic :: Software Development :: Libraries :: Python Modules'
]


if v[2] == '*final':
  classifiers.append('Development Status :: 5 - Production/Stable')
else:
  classifiers.append('Development Status :: 4 - Beta')


# -----------------------------------------
# Helpers
from distutils.dir_util import remove_tree

def read(*rnames):
  return open(os.path.join(*rnames)).read()

def rm_file(path):
  if os.access(path, os.F_OK):
    os.remove(path)
    log.info('removed file %s', path)

def rm_dir(path):
  if os.access(path, os.F_OK):
    remove_tree(path)
    log.info('removed directory %s', path)

import shutil
copy_file = shutil.copy

def shell_cmd(args, cwd=BASE_DIR):
  '''Returns stdout as string or None on failure
  '''
  if not isinstance(args, (list, tuple)):
    args = [args]
  ps = Popen(args, shell=True, cwd=cwd, stdout=PIPE, stderr=PIPE,
             close_fds=True)
  stdout, stderr = ps.communicate()
  if ps.returncode != 0:
    if stderr:
      stderr = stderr.strip()
    raise IOError('Shell command %s failed (exit status %r): %s' %\
      (args, ps.returncode, stderr))
  return stdout.strip()


_core_build_id = None
def core_build_id():
  '''Unique id in URN form, distinguishing each unique build.
  
  If building from a repository checkout, the resulting string
  will have the format "urn:rcsid:IDENTIFIER[+DIRTY]". If building
  from source which is not under revision control, the build id 
  will have the format "urn:utcts:YYYYMMDDHHMMSS". (UTC timestamp)
  
  In the special case of a Debian package, there is a suffix of
  the following format: ":debian:" package-revision
  Examples of Debianized build ids:
    urn:rcsid:1bb4cbff6045:debian:3
    urn:utcts:20081030020621:debian:3
  
  Dirty repositories generate a urn:rcsid with a trailing "+"
  followed by a base 16 encoded timestamp.
  
  A "unique build" is defined as the sum of all source code bytes
  combined. A single modification anywhere causes a new unique
  instance to be "born".
  
  This value can be overridden by exporting the SMISK_BUILD_ID
  environment variable, but keep in mind to use a URN av value.
  
  :return: URN
  :rtype: string
  '''
  global _core_build_id
  if _core_build_id is None:
    if 'SMISK_BUILD_ID' in os.environ:
      _core_build_id = os.environ['SMISK_BUILD_ID']
    else:
      # Maybe under revision control
      try:
        _core_build_id = shell_cmd(['git rev-parse master'])
      except IOError:
        pass
      if _core_build_id:
        dirty_extra = ''
        if _core_build_id[-1] == '+':
          dirty_extra = '%x' % int(time.time())
        _core_build_id = 'urn:rcsid:%s%s' % (_core_build_id, dirty_extra)
        if 'SMISK_BUILD_ID_SUFFIX' in os.environ:
          _core_build_id += os.environ['SMISK_BUILD_ID_SUFFIX']
      if not _core_build_id:
        # Not under revision control
        _core_build_id = time.strftime('urn:utcts:%Y%m%d%H%M%S', time.gmtime())
  return _core_build_id

if '--print-build-id' in sys.argv:
  print core_build_id()
  sys.exit(0)

# -----------------------------------------
# Commands

class Extension(_Extension):
  def built_product_path(self, build_dir):
    relpath = self.name.split('.')
    path = os.path.join(build_dir, *relpath[:-1])
    match_prefix = '%s.' % relpath[-1]
    for f in os.listdir(path):
      if f.startswith(match_prefix):
        fn = os.path.join(path, f)
        if not os.path.isdir(fn):
          return fn
  

from distutils.command.build import build as _build
class build(_build):
  description = 'will build the whole package'
  user_options = _build.user_options
  user_options.append(
    ('debug-smisk', None, "compile Smisk with debugging information. Implies --debug"),
  )
  boolean_options = _build.boolean_options
  boolean_options.append('debug_smisk')
  sub_commands = [('build_py',      _build.has_pure_modules),
                  ('build_clib',    _build.has_c_libraries),
                  ('build_ext',     _build.has_ext_modules),
                  ('build_scripts', _build.has_scripts),
                 ]
  
  def initialize_options(self):
    _build.initialize_options(self)
    self.debug_smisk = False
  

from setuptools.command.build_ext import build_ext as _build_ext
class build_ext(_build_ext):
  description = 'Build smisk.core C extension (compile/link to build directory)'
  
  def finalize_options(self):
    _build_ext.finalize_options(self)
    
    # Process BSDDB module build
    import setup_bsddb
    self.bsddb = setup_bsddb
    
    self.include_dirs.extend([
      '/usr/include',
      '/usr/local/include',
      '/usr/include'])
    self.library_dirs.extend([
      '/lib64',
      '/usr/lib64',
      '/lib',
      '/usr/lib',
      '/usr/local/lib'])
    
    self.include_dirs.append(self.bsddb.incdir)
    self.library_dirs.append(self.bsddb.libdir)
    
    self.libraries.extend(['fcgi', self.bsddb.dblib])
    self.define = [
      ('SMISK_VERSION', '"%s"' % version),
      ('SMISK_BUILD_ID', '"%s"' % core_build_id()),
    ]
    self.undef = []
  
  def run(self):
    self._run_config_if_needed()
    self._check_prefix_modified()
    self._configure_compiler()
    
    log.info('include dirs: %r', self.include_dirs)
    log.info('library dirs: %r', self.library_dirs)
    
    _build_ext.run(self)
  
  def built_product_paths(self):
    product_paths = []
    for ext in self.extensions:
      path = ext.built_product_path(self.build_lib)
      if path:
        product_paths.append(path)
    return product_paths
  
  def resolve_local_imports(self, fn, paths):
    include_re = re.compile(r'^\s*#(?:include|import)\s+"([^"]+)"', re.I)
    fdir = os.path.dirname(fn)
    f = open(fn, 'r')
    try:
      for line in f:
        m = include_re.match(line)
        if m:
          include_fn = os.path.abspath(os.path.join(fdir, m.group(1)))
          if include_fn not in paths:
            paths.append(include_fn)
            self.resolve_local_imports(include_fn, paths)
    finally:
      f.close()
  
  def find_precompiled(self):
    prefix_h = os.path.abspath('src/prefix.h')
    paths = [prefix_h]
    self.resolve_local_imports(prefix_h, paths)
    return paths
  
  def _check_prefix_modified(self):
    if self.force:
      return
    built_product_paths = self.built_product_paths()
    for precompiled_fn in self.find_precompiled():
      precompiled_mt = os.path.getmtime(precompiled_fn)
      for product_fn in built_product_paths:
        if precompiled_mt > os.path.getmtime(product_fn):
          log.info('Precompiled file %s have been modified -- forcing complete rebuild', precompiled_fn)
          self.force = True
          break
      if self.force:
        break
  
  def _run_config_if_needed(self):
    run_configure = True
    try:
      # If system_config.h is newer than this file and exists: don't create it again.
      if os.path.getmtime(SYS_CONF_H) > os.path.getmtime(__file__):
        run_configure = False
    except os.error:
      pass
    if run_configure or self.force:
      self.run_command('config')
  
  def _configure_compiler(self):
    global cflags, include_dirs, library_dirs, libraries, version
    machine = platform.machine()
    log.debug("Configuring compiler...")
    
    cflags = ' -include "%s"' % os.path.realpath(os.path.join(
      os.path.dirname(__file__), "src", "prefix.h"))
    
    # Warning flags
    warnings = ['all', 'no-unknown-pragmas']
    cflags += ''.join([' -W%s' % w for w in warnings])
    
    if '--debug' in sys.argv or '--debug-smisk' in sys.argv:
      log.debug("Mode: debug -- setting appropriate cflags and macros")
      self.debug = True
      cflags += ' -O0'
      self.define.append(('DEBUG', '1'))
      if '--debug-smisk' in sys.argv:
        log.info("Enabling Smisk debug messages")
        self.define.append(('SMISK_DEBUG', '1'))
    else:
      log.debug("Mode: release -- setting appropriate cflags and macros")
      self.debug = False
      cflags += ' -Os'
      if machine in X86_MACHINES:
        log.debug("Enabling SSE3 support")
        cflags += ' -msse3'
        if platform.system() == 'Darwin':
          cflags += ' -mssse3'
    # set c flags
    if 'CFLAGS' in os.environ:
      os.environ['CFLAGS'] += cflags
    else:
      os.environ['CFLAGS'] = cflags
  

from distutils.command.config import config as _config
class config(_config):
  description = 'Configure build (almost like "./configure")'
  
  def initialize_options (self):
    global include_dirs, libraries
    _config.initialize_options(self)
    self.noisy = 0
    self.dump_source = 0
    self.macros = {}
  
  def run(self):
    self._machine()
    self._headers()
    self._libraries()
    self._write_system_config_h()
  
  def _silence(self):
    self.orig_log_threshold = log._global_log.threshold
    log._global_log.threshold = log.WARN
  
  def _unsilence(self):
    log._global_log.threshold = self.orig_log_threshold
  
  def check_header(self, *args, **kwargs):
    self._silence()
    r = _config.check_header(self, *args, **kwargs)
    self._unsilence()
    return r
  
  def _machine(self):
    # Alignment
    machine = platform.machine()
    log.info('checking machine alignment')
    if machine in X86_MACHINES:
      log.debug('non-aligned')
      self.macros['SMISK_SYS_NONALIGNED'] = 1
    else:
      log.debug('aligned')
    # Endianess
    log.info('checking machine endianess')
    test = self._run('''
    int main (int argc, const char * argv[]) {
      int i = 0x11223344;
      char *p = (char *) &i;
      if (*p == 0x44) return 0;
      return 1;
    }
    ''')
    if test == 0:
      self.macros['SMISK_SYS_LITTLE_ENDIAN'] = 1
      log.debug("little endian")
    else:
      log.debug("big endian")
  
  def _headers(self):
    defname_re = re.compile('[^a-zA-Z_]')
    for fn in HAVE_HEADERS:
      log.info('checking for header %s', fn)
      if self.check_header(header=fn):
        log.debug("found %s", fn)
        self.macros['HAVE_%s' % defname_re.sub('_', fn).upper()] = 1
      else:
        log.debug("missing")
  
  def _libraries(self):
    global required_libraries, libraries
    for n in [('fcgi', ['fastcgi.h', 'fcgiapp.h'])]:
      log.info('checking for library %s', n[0])
      sys.stdout.flush()
      self._silence()
      ok = self.check_lib(library=n[0], headers=n[1])
      self._unsilence()
      if not ok:
        log.error("missing required library %s" % n[0])
        sys.exit(1)
  
  def _run(self, body, headers=None, include_dirs=None, libraries=None, library_dirs=None, lang='c'):
    self._silence()
    self._check_compiler()
    (src, obj, prog) = self._link(body=body, headers=headers, include_dirs=[], 
                                  libraries=libraries, library_dirs=library_dirs, lang=lang)
    self._unsilence()
    if prog.find('/') == -1:
      prog = './' + prog
    ps = Popen(shell=True, args=[prog])
    exit_code = ps.wait()
    self._clean()
    return exit_code
  
  def _write_system_config_h(self):
    import re
    f = open(SYS_CONF_H, "w")
    try:
      try:
        f.write("/* Generated by setup.py at %s */\n" % time.strftime("%c %z"))
        f.write("#ifndef SMISK_SYSTEM_CONFIG_H\n")
        f.write("#define SMISK_SYSTEM_CONFIG_H\n\n")
        for k,v in self.macros.items():
          f.write("#ifndef %s\n" % k)
          f.write(" #define %s %s\n" % (k, str(v)) )
          f.write("#endif\n")
        f.write("\n#endif\n")
        log.info('wrote compile-time configuration to %s', SYS_CONF_H)
      finally:
        f.close()
    except:
      os.remove(SYS_CONF_H)
      raise
  

class sphinx_build(Command):
  description = 'build documentation using Sphinx if available'
  user_options = [
    ('builder=', 'b', 'builder to use; default is html'),
    ('all', 'a', 'write all files; default is to only write new and changed files'),
    ('reload-env', 'E', "don't use a saved environment, always read all files"),
    ('source-dir=', 's', 'path where sources are read from (default: docs/source)'),
    ('out-dir=', 'o', 'path where output is stored (default: docs/<builder>)'),
    ('cache-dir=', 'd', 'path for the cached environment and doctree files (default: outdir/.doctrees)'),
    ('conf-dir=', 'c', 'path where configuration file (conf.py) is located (default: same as source-dir)'),
    ('set=', 'D', '<setting=value> override a setting in configuration'),
    ('no-color', 'N', 'do not do colored output'),
    ('pdb', 'P', 'run Pdb on exception'),
  ]
  boolean_options = ['all', 'reload-env', 'no-color', 'pdb']
  
  def initialize_options(self):
    self.sphinx_args = []
    self.builder = None
    self.all = False
    self.reload_env = False
    self.source_dir = None
    self.out_dir = None
    self.cache_dir = None
    self.conf_dir = None
    self.set = None
    self.no_color = False
    self.pdb = False
  
  def finalize_options(self):
    self.sphinx_args.append('sphinx-build')
    
    if self.builder is None:
      self.builder = 'html'
    self.sphinx_args.extend(['-b', self.builder])
    
    if self.all:
      self.sphinx_args.append('-a')
    if self.reload_env:
      self.sphinx_args.append('-E')
    if self.no_color or ('PS1' not in os.environ and 'PROMPT_COMMAND' not in os.environ):
      self.sphinx_args.append('-N')
    if not self.distribution.verbose:
      self.sphinx_args.append('-q')
    if self.pdb:
      self.sphinx_args.append('-P')
    
    if self.cache_dir is not None:
      self.sphinx_args.extend(['-d', self.cache_dir])
    if self.conf_dir is not None:
      self.sphinx_args.extend(['-c', self.conf_dir])
    if self.set is not None:
      self.sphinx_args.extend(['-D', self.set])
    
    if self.source_dir is None:
      self.source_dir = os.path.join('docs', 'source')
    if self.out_dir is None:
      self.out_dir = os.path.join('docs', self.builder)
    
    self.sphinx_args.extend([self.source_dir, self.out_dir])
  
  def run(self):
    try:
      import sphinx
      if not os.path.exists(self.out_dir):
        if self.dry_run:
          self.announce('skipping creation of directory %s (dry run)' % self.out_dir)
        else:
          self.announce('creating directory %s' % self.out_dir)
          os.makedirs(self.out_dir)
      
      if self.dry_run:
        self.announce('skipping %s (dry run)' % ' '.join(self.sphinx_args))
      else:
        self.announce('running %s' % ' '.join(self.sphinx_args))
        sphinx.main(self.sphinx_args)
    except ImportError, e:
      log.info('Sphinx not installed -- skipping documentation. (%s)', e)
  


class debian(Command):
  description = 'build debian packages'
  user_options = [
    ('upload', 'u',       'upload resulting package using dupload'),
    ('binary-only', 'b',  'indicates that no source files are to be built and/or distributed'),
    ('source-only', 'S',  'specifies that only the source should be uploaded and no binary '\
                          'packages need to be made'),
    ('key-id=', 'k',      'specify a key-ID to use when signing packages'),
  ]
  boolean_options = ['upload', 'binary', 'source']
  
  def initialize_options(self):
    self.args = []
    self.upload = False
    self.binary_only = False
    self.source_only = False
    self.key_id = None
  
  def finalize_options(self):
    self.args.append('admin/dist-debian.sh')
    if self.upload:
      self.args.append('-u')
    if self.binary_only and self.source_only:
      raise Exception('arguments --binary-only and --source-only can not be used together')
    elif self.binary_only:
      self.args.append('-b')
    elif self.source_only:
      self.args.append('-S')
    if self.key_id:
      self.args.append('-k'+self.key_id)
  
  def run(self):
    cmd = ' '.join(self.args)
    if self.dry_run:
      self.announce('skipping %s (dry run)' % cmd)
    else:
      self.announce('running %s' % cmd)
      status = subprocess.call(cmd, shell=True)
      if status != 0:
        sys.exit(status)
  


from distutils.command.clean import clean as _clean
class clean(_clean):
  def run(self):
    _clean.run(self)
    log.info('Removing files generated by setup.py')
    for path in ['MANIFEST', 'src/system_config.h']:
      rm_file(path)
    log.info('Removing generated documentation')
    rm_dir('docs/html')
    rm_dir('docs/latex')
    rm_dir('docs/pdf')
  

from setuptools.command.sdist import sdist as _sdist
class sdist(_sdist):
  def run(self):
    try:
      _sdist.run(self)
    finally:
      for path in ['MANIFEST']:
        rm_file(path)
  


# -----------------------------------------

class SmiskDistribution(Distribution):
  def __init__(self, attrs=None):
    Distribution.__init__(self, attrs)
    self.cmdclass = {
      'build': build,
      'build_ext': build_ext,
      'sdist': sdist,
      'config': config,
      'docs': sphinx_build,
      'clean': clean,
    }
    try:
      shell_cmd('which dpkg-buildpackage')
      self.cmdclass['debian'] = debian
    except IOError:
      # Not a debian system or dpkg-buildpackage not installed
      pass
  

# -----------------------------------------

setup(
  distclass = SmiskDistribution,
  name = "smisk",
  version = version,
  author = author,
  author_email = email,
  license = license,
  description = "High-performance web service framework",
  long_description = (
    "\n"+read('README.rst')
    + "\n"
    + read('CHANGELOG.rst')
    + "\n"
    'License\n'
    '=======\n'
    + read('LICENSE')
    + '\n'
    'Download\n'
    '========\n'
  ),
  url = 'http://python-smisk.org/',
  platforms = "ALL",
  classifiers = classifiers,
  zip_safe = False, # I don't like zipped eggs. However Smisk _can_ be zip-egged.
  package_dir = {'': 'lib'},
  packages = [
    'smisk',
    'smisk.core',
    'smisk.inflection',
    'smisk.ipc',
    'smisk.mvc',
    'smisk.mvc.template',
    'smisk.serialization',
    'smisk.util',
    'smisk.test',
    'smisk.test.core',
    'smisk.test.live',
    'smisk.test.mvc',
    'smisk.test.util',
  ],
  include_package_data=True,
  exclude_package_data={"debian" : ["*"]},
  ext_modules = [Extension(
    name = '_smisk',
    sources = sources,
    undef_macros = undef_macros
  )],
  test_suite = 'smisk.test',
  extras_require={
    'serialization': ['python-cjson'], # or minjson
  },
)
