#!/usr/bin/env python
# encoding: utf-8
from distutils.core import setup, Extension
from distutils.cmd import Command
import os, sys

version = "0.1"

sources = ['src/module.c',
           'src/Application.c',
           'src/Request.c',
           'src/Response.c',
           'src/Stream.c', 
           'src/NotificationCenter.c',
           'src/utils.c',
           'src/URL.c',
           'src/atoin.c']

os.chdir(os.path.join('.', os.path.dirname(__file__)))

# get revision
try:
  (child_stdin, child_stdout) = os.popen2('svnversion -n .')
  revision = child_stdout.read()
  p = revision.rfind(':')
  if p != -1:
    revision = revision[p+1:]
  revision = revision.replace('M','').replace('S','')
  version += "r" + revision
except:
  pass

include_dirs = ['/opt/local/include', '/usr/local/include', '/usr/include']
library_dirs = ['/opt/local/lib', '/usr/local/lib', '/usr/lib']
libraries = ['fcgi'] # to link with
runtime_library_dirs = []
extra_objects = []

#---------------------------------------

class build_doc(Command):
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
  


# write version.h
f = open(os.path.abspath(os.path.join(os.path.dirname(__file__), "src/version.h")), "w")
try: f.write("#ifndef SMISK_VERSION\n#define SMISK_VERSION \"%s\"\n#endif\n" % version)
finally: f.close()

setup (name = "smisk",
  version = version,
  description = "Minimal FastCGI-based web application framework",
  author = 'Rasmus Andersson',
  author_email = 'rasmus@flajm.se',
  license = 'MIT',
  url = 'http://trac.hunch.se/pyfcgi',
  
  ext_modules = [Extension( name='smisk',
    sources=sources,
    include_dirs=include_dirs,
    library_dirs=library_dirs,
    runtime_library_dirs=runtime_library_dirs,
    libraries=libraries,
    extra_objects=extra_objects
  )],
  
  cmdclass={'build_doc': build_doc, 'docs': build_doc}
)
