#!/usr/bin/env python
# encoding: utf-8
from distutils.core import setup, Extension
from distutils.cmd import Command
from distutils.command.build import build as build_cmd
import os, sys, platform

version = "0.1.0"

sources = ['src/__init__.c',
           
           'src/utils.c',
           'src/atoin.c',
           'src/cstr.c',
           'src/multipart.c',
           'src/sigsegv.c',
           
           'src/Application.c',
           'src/Request.c',
           'src/Response.c',
           'src/Stream.c', 
           'src/NotificationCenter.c',
           'src/URL.c',
           'src/FileSessionStore.c',
           
              'src/xml/__init__.c']

os.chdir(os.path.join('.', os.path.dirname(__file__)))
py_version = ".".join([str(s) for s in sys.version_info[0:2]]) # "M.m"

# get revision
revision = ''
try:
  (child_stdin, child_stdout) = os.popen2('svnversion -n .')
  revision = child_stdout.read()
  version += '-r' + revision
except:
  pass

include_dirs = ['/usr/include/python%s' % py_version, # debian and others
                '/opt/local/include/python%s' % py_version, # bsd ports, mac ports, etc
                '/usr/local/include', # general
                '/usr/include']       # general

library_dirs = ['/opt/local/lib',
                '/usr/local/lib',
                '/usr/lib']

libraries = ['fcgi'] # to link with

runtime_library_dirs = []
extra_objects = []
define_macros = []
undef_macros = []
cflags = ' -Wall'

#---------------------------------------
# Commands

class apidocs(Command):
  description = 'Builds the documentation'
  user_options = []
  def initialize_options(self): pass
  def finalize_options(self): pass
  def run(self):
    try:
      from epydoc import cli
      old_argv = sys.argv[1:]
      sys.argv[1:] = [
        '--config=doc/epydoc.conf',
        '--no-private', # epydoc bug, not read from config
        #'--verbose',
        '--simple-term'
      ]
      print 'cli=', cli
      cli.cli()
      sys.argv[1:] = old_argv
    except ImportError:
      print 'epydoc not installed, skipping API documentation.'
  


#---------------------------------------
# write version.h
f = open(os.path.abspath(os.path.join(os.path.dirname(__file__), "src/version.h")), "w")
try:
  f.write("#ifndef SMISK_VERSION\n#define SMISK_VERSION \"%s\"\n#endif\n" % version)
  f.write("#ifndef SMISK_REVISION\n#define SMISK_REVISION \"%s\"\n#endif\n" % revision)
finally: f.close()

# set compiler options
if '--debug' in sys.argv:
  define_macros = [('SMISK_DEBUG', '1')]
  undef_macros = ['NDEBUG']
else:
  if platform.machine().find('x86') != -1:
    cflags += ' -msse3'
    if platform.system() == 'Darwin':
      cflags += ' -mssse3'

# set c flags
if 'CFLAGS' in os.environ: os.environ['CFLAGS'] += cflags
else: os.environ['CFLAGS'] = cflags

#---------------------------------------
setup (
  name = "smisk",
  version = version,
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
    include_dirs=include_dirs,
    library_dirs=library_dirs,
    runtime_library_dirs=runtime_library_dirs,
    libraries=libraries,
    extra_objects=extra_objects,
    define_macros=define_macros,
    undef_macros=undef_macros
  )],
  
  cmdclass={'apidocs': apidocs}
)
