#!/usr/bin/env python
#----------------------------------------------------------------------
# Setup script for the bsddb3 package

import os
import re
import sys
import glob

from distutils.dep_util import newer
from distutils import log
import distutils.ccompiler

# read the module version number out of the .c file
VERSION = None
try:
  f = open('src/bsddb.h', 'r')
except IOError, e:
  raise RuntimeError("Could not open src/bsddb.h source to read the version number. %s" % e)
_ver_re = re.compile('^#\s*define\s+PY_BSDDB_VERSION\s+"(\d+\.\d+\.\d+.*)"')
for line in f.readlines():
  m = _ver_re.match(line)
  if m:
    VERSION = m.group(1)
    continue
f.close()
del f
del _ver_re
del m
if not VERSION:
  raise RuntimeError("could not find PY_BSDDB_VERSION in src/bsddb.h")

#----------------------------------------------------------------------

debug = '--debug' in sys.argv or '-g' in sys.argv

lflags_arg = []


if os.name == 'posix':
  # Allow setting the DB dir and additional link flags either in
  # the environment or on the command line.
  # First check the environment...
  BERKELEYDB_INCDIR = os.environ.get('BERKELEYDB_INCDIR', '')
  BERKELEYDB_LIBDIR = os.environ.get('BERKELEYDB_LIBDIR', '')
  BERKELEYDB_DIR = os.environ.get('BERKELEYDB_DIR', '')
  LFLAGS = os.environ.get('LFLAGS', [])
  LIBS = os.environ.get('LIBS', [])

  # ...then the command line.
  # Handle --berkeley-db=[PATH] and --lflags=[FLAGS]
  args = sys.argv[:]
  for arg in args:
    if arg.startswith('--berkeley-db-incdir='):
      BERKELEYDB_INCDIR = arg.split('=')[1]
      sys.argv.remove(arg)
    if arg.startswith('--berkeley-db-libdir='):
      BERKELEYDB_LIBDIR = arg.split('=')[1]
      sys.argv.remove(arg)
    if arg.startswith('--berkeley-db='):
      BERKELEYDB_DIR = arg.split('=')[1]
      sys.argv.remove(arg)
    elif arg.startswith('--lflags='):
      LFLAGS = arg.split('=')[1].split()
      sys.argv.remove(arg)
    elif arg.startswith('--libs='):
      LIBS = arg.split('=')[1].split()
      sys.argv.remove(arg)

  if LFLAGS or LIBS:
    lflags_arg = LFLAGS + LIBS

  # If we were not told where it is, go looking for it.
  dblib = 'db'
  incdir = libdir = None
  if not BERKELEYDB_DIR and not BERKELEYDB_LIBDIR and not BERKELEYDB_INCDIR:
    # NOTE: when updating these, also change the tuples in the for loops below
    max_db_ver = (4, 7)
    min_db_ver = (4, 0)

    # construct a list of paths to look for the header file in on
    # top of the normal inc_dirs.
    db_inc_paths = [
      '/usr/include/db4',
      '/usr/local/include/db4',
      '/opt/sfw/include/db4',
      '/sw/include/db4',
      '/usr/include/db3',
      '/usr/local/include/db3',
      '/opt/sfw/include/db3',
      '/opt/local/include/db4',
      '/sw/include/db3',
    ]
    # 4.x minor number specific paths
    for x in range(max_db_ver[1]+1):
      db_inc_paths.append('/usr/include/db4%d' % x)
      db_inc_paths.append('/usr/local/BerkeleyDB.4.%d/include' % x)
      db_inc_paths.append('/usr/local/include/db4%d' % x)
      db_inc_paths.append('/pkg/db-4.%d/include' % x)
      db_inc_paths.append('/opt/db-4.%d/include' % x)
      db_inc_paths.append('/opt/local/include/db4%d' % x)
    # 3.x minor number specific paths
    for x in (2,3):
      db_inc_paths.append('/usr/include/db3%d' % x)
      db_inc_paths.append('/usr/local/BerkeleyDB.3.%d/include' % x)
      db_inc_paths.append('/usr/local/include/db3%d' % x)
      db_inc_paths.append('/pkg/db-3.%d/include' % x)
      db_inc_paths.append('/opt/db-3.%d/include' % x)
      db_inc_paths.append('/opt/local/include/db3%d' % x)

    db_ver_inc_map = {}

    class db_found(Exception): pass
    try:
      # this CCompiler object is only used to locate include files
      compiler = distutils.ccompiler.new_compiler()

      lib_dirs = compiler.library_dirs + [
        '/lib64', '/usr/lib64',
        '/lib', '/usr/lib',
        '/opt/local/lib/db46' # xxx todo
      ]
      inc_dirs = compiler.include_dirs + ['/usr/include']

      # See whether there is a Oracle or Sleepycat header in the standard
      # search path.
      for d in inc_dirs + db_inc_paths:
        f = os.path.join(d, "db.h")
        log.debug("db: looking for db.h in %s", f)
        db_ver = (0, 0)
        if os.path.exists(f):
          f = open(f).read()
          m = re.search(r"#define\WDB_VERSION_MAJOR\W(\d+)", f)
          if m:
            db_major = int(m.group(1))
            m = re.search(r"#define\WDB_VERSION_MINOR\W(\d+)", f)
            db_minor = int(m.group(1))
            db_ver = (db_major, db_minor)

            if ( (not db_ver_inc_map.has_key(db_ver)) and
               (db_ver <= max_db_ver and db_ver >= min_db_ver) ):
              # save the include directory with the db.h version
              # (first occurrance only)
              db_ver_inc_map[db_ver] = d
              log.debug("db.h: found %s in %s", db_ver, d)
            else:
              # we already found a header for this library version
              log.debug("db.h: ignoring %s", d)
          else:
            # ignore this header, it didn't contain a version number
            log.debug("db.h: unsupported version %s in %s", db_ver, d)

      db_found_vers = db_ver_inc_map.keys()
      db_found_vers.sort()

      while db_found_vers:
        db_ver = db_found_vers.pop()
        db_incdir = db_ver_inc_map[db_ver]

        # check lib directories parallel to the location of the header
        db_dirs_to_check = [
          os.path.join(db_incdir, '..', 'lib64'),
          os.path.join(db_incdir, '..', 'lib'),
          os.path.join(db_incdir, '..', '..', 'lib64'),
          os.path.join(db_incdir, '..', '..', 'lib'),
        ]
        db_dirs_to_check = filter(os.path.isdir, db_dirs_to_check)

        # Look for a version specific db-X.Y before an ambiguoius dbX
        # XXX should we -ever- look for a dbX name?  Do any
        # systems really not name their library by version and
        # symlink to more general names?
        for dblib in (('db-%d.%d' % db_ver), ('db%d' % db_ver[0])):
          dblib_file = compiler.find_library_file(
                  db_dirs_to_check + lib_dirs, dblib )
          if dblib_file:
            db_libdir = os.path.abspath(os.path.dirname(dblib_file))
            raise db_found
          else:
            log.debug("db lib: %s not found", dblib)
    except db_found:
      log.info("Found Berkeley DB %d.%d installation.", *db_ver)
      log.info("  include files in %s", db_incdir)
      log.info("  library files in %s", db_libdir)
      log.info("  library name is lib%s", dblib)
      log.debug("db: lib dir: %s, include dir: %s", db_libdir, db_incdir)

      incdir  = db_incdir
      libdir  = db_libdir
    else:
      # this means Berkeley DB could not be found
      pass

  if BERKELEYDB_LIBDIR or BERKELEYDB_INCDIR:
    libdir = BERKELEYDB_LIBDIR or None
    incdir = BERKELEYDB_INCDIR or None

  if not BERKELEYDB_DIR and not incdir and not libdir:
    raise EnvironmentError("Can't find a local Berkeley DB installation.\n"\
      "(suggestion: try the --berkeley-db=/path/to/bsddb option)")

  # figure out from the base setting where the lib and .h are
  if not incdir:
    incdir = os.path.join(BERKELEYDB_DIR, 'include')
  if not libdir:
    libdir = os.path.join(BERKELEYDB_DIR, 'lib')
  if not '-ldb' in LIBS:
    libname = [dblib]
  else:
    log.debug("db: LIBS already contains '-ldb' not adding our own '-l%s'", dblib)
    libname = []
  utils = []

  # Test if the old bsddb is built-in
  static = 0
  try:
    import bsddb
    if str(bsddb).find('built-in') >= 0:
      static = 1
  except ImportError:
    pass

  # On Un*x, double check that no other built-in module pulls libdb in as a
  # side-effect. TBD: how/what to do on other platforms?
  fp = os.popen('ldd %s 2>&1' % sys.executable)
  results = fp.read()
  status = fp.close()
  if not status and results.find('libdb.') >= 0:
    static = 1

  if static:
    print """\
\aWARNING:
\tIt appears that the old bsddb module is staticly linked in the
\tPython executable. This will cause various random problems for
\tbsddb3, up to and including segfaults. Please rebuild your
\tPython either with bsddb disabled, or with it built as a shared
\tdynamic extension. Watch out for other modules (e.g. dbm) that create
\tdependencies in the python executable to libdb as a side effect."""
    st = raw_input("Build anyway? (yes/[no]) ")
    if st != "yes":
      sys.exit(1)


elif os.name == 'nt':
  print >> sys.stderr, 'Windows is not (yet) supported'



# include_dirs = [ incdir ],
# define_macros = [('PYBSDDB_STANDALONE', 1)],
# library_dirs = [ libdir ],
# runtime_library_dirs = [ libdir ],
# libraries = libname,
# extra_link_args = lflags_arg,