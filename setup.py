#!/usr/bin/env python
# encoding: utf-8
from distutils.core import setup, Extension
from distutils.cmd import Command
import os, sys

sources = ['src/module.c', 'src/Request.c', 'src/Stream.c']
revision = int("$ProjectRevision: 26$".split(' ')[1][:-1])
version = "0.1.%d" % revision

include_dirs = ['/usr/include', '/usr/local/include']
library_dirs = ['/usr/lib', '/usr/local/lib']
libraries = ['fcgi']
runtime_library_dirs = []
extra_objects = []

#---------------------------------------

class build_doc(Command):
	description = 'Builds the documentation'
	user_options = []
	
	def initialize_options(self):
		pass
	
	def finalize_options(self):
		pass
	
	def run(self):
		epydoc_conf = os.path.join('doc', 'epydoc.conf')
		try:
			from epydoc import cli
			old_argv = sys.argv[1:]
			sys.argv[1:] = [
				'--config=%s' % epydoc_conf,
				'--no-private', # epydoc bug, not read from config
				#'--verbose',
				'--simple-term'
			]
			cli.cli()
			sys.argv[1:] = old_argv
		except ImportError:
			print 'epydoc not installed, skipping API documentation.'
	


# write version.h
f = open(os.path.abspath(os.path.join(os.path.dirname(__file__), "src/version.h")), "w")
try: f.write("#ifndef PY_FCGI_VERSION\n#define PY_FCGI_VERSION \"%s\"\n#endif\n" % version)
finally: f.close()

setup (name = "py-fcgi",
	version = version,
	description = "FastCGI library with thread safety",
	#platforms = "i386",
	author = 'Rasmus Andersson',
	author_email = 'rasmus@flajm.se',
	license = 'MIT',
	url = 'http://trac.hunch.se/pyfcgi',
	
	ext_modules = [Extension( name='fcgi',
		sources=sources,
		include_dirs=include_dirs,
		library_dirs=library_dirs,
		runtime_library_dirs=runtime_library_dirs,
		libraries=libraries,
		extra_objects=extra_objects
	)],
	
	cmdclass={'build_doc': build_doc, 'docs': build_doc}
)
