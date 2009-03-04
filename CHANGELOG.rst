Changes
=======

1.1.4
-----

* Removed the bsddb module -- the smisk.ipc.bsddb module still exist, but
  required an external bsddb module to be installed.


1.1.3
-----

* Fixed a bug with parameter keys not being normalized to unicode.

* Reworked Elixir/SQLAlchemy handling of sessions during HTTP transactions.

* Only a subset of the built-in serializers are loaded by default, rather than
  all. There's a new module called smisk.serialization.all which can be
  imported in order to load all built-in serializers.

* Serializers now need to excplicitly specify their read/write capabilities
  using two boolean attributes: can_serialize and can_unserialize.
  BaseSerializer defines both of these as False.

* plist serializer reworked to use plistlib, which has been modified to support
  serialization of Elixir Entities (database objects).

* New generic XML serializer smisk.serialization.xmlgeneric (not loaded by 
  default).

* smisk.mvc.Request instances have a new attribute called cn_url. The value is
  a smisk.core.URL instance which is guaranteed *not* to include any filename
  extension. cn_url is a copy of Request.url if the request was made without
  the canonical path (i.e. not including filename extension. "/foo/bar" instead
  of "/foo/bar.json"). Otherwise cn_url is a modified copy of url. This is
  useful for building paths based on the request path wihout having to know if
  there's a filename extension involved or not.

* Leaf filters can now be created as pythonic decorators using the aiding
  decorator leaf_filter, found in smisk.mvc.decorators. See
  http://python-smisk.org/docs/1.1.3/library/smisk.mvc.html#leaf-filters
  for more information.

* The previously built-in crash reporter is no longer built by default. Can be
  enabled by defining the macro SMISK_ENABLE_CRASH_REPORTING 1 (more info in 
  src/config.h).

* Major documentation update.

* Various minor fixes.


1.1.2
-----

* Inter-process communication module smisk.ipc, providing a shared dictionary
  which can be concurrently manipulated by a set of processes.

* Berkely DB module smisk.core.bsddb

* Benchmark utility module smisk.util.benchmark exposes an iterator which can
  be used to easily benchmark snippets of code.
  
* The key-value store example application now uses the shared dictionary
  provided by smisk.ipc.

* smisk.core.Request have two soft limits – max_multipart_size and 
  max_formdata_size – for limiting automatically handled input data size. These
  soft limits can also be used to disable the automated parsing of Smisk.

* smisk.util.cache has a new function – app_shared_key – returning a byte
  string which can be used to uniqely identify the application. The key is
  based on the entry file (the python file in which __name__ == "__main__").

* smisk.util.type exposes MutableMapping – in Python >=2.6 this is 
  collections.MutableMapping, in Python >=2.3 it is UserDict.DictMixin.

* Serializers no longer emit warning.warn-messages when no suiting
  implementations are available. Now they are simply not registered whitout as
  much as a whisper.

* In the C library, the macro SMISK_PyString_Check has changed name to 
  SMISK_STRING_CHECK (however it still does the exact same thing as before,
  just that in preparation for porting Smisk to Python 3, we need to sort out
  the different meanings of "bytes strings" and "character strings")

* In the C library, we use PyBytes instead of PyString and NUMBER_* instead of
  some PyInt-functions, having macros for Python <2.5. This is a step toward
  the Python 3 port.

* smisk.core is now stored as _smisk and imported by smisk/core/__init__.py.
  This follows the naming custom of other machine-native modules as well as
  provides better name (i.e. _smisk.so instead of core.so) in various listings.

* Fixed a bug in smisk.core where a www-form-urlencoded request with incorrect
  content length and the first key was longer than the provided content length,
  smisk would induce strange errors (because trying to set NULL into a python
  dict).


1.1.1
-----

* Fully unicode on the inside -- request.get, .post, .cookies, etc return
  unicode values and where dictionary keys are used, which have been translated
  from the outside world, they are guranteeded to be encoded as UTF-8.
  (Dictionary keys used as keyword arguments must be str in Python <=2.5)

* YAML read/write-serialization #21 [a72dc2f0855b]

* Handles and reconnects dead MySQL-connections. #23 [49cb2034a8b1]

* No longer stores empty parts as None from multipart messages. #15
  [d9920fb75ca2]

* Makes full use of HTTP 1.1 request methods (OPTIONS, GET, HEAD, PUT, POST,
  DELETE). See example application: examples/mvc/key-value-store/

* smisk.mvc.model no longer disposes SA/Elixir sessions for each request, but
  tries to reuse a session as long as no error occur.

* redirect_to() respects and retains explicit request format, denoted by path
  extension in the original request.

* smisk.test.live introduces "live" tests, running a server and a client,
  measuring communication and effects.


1.1.0
-----

* MVC module – smisk.mvc.

* Better unicode support.

* Compatible with Debian Etch.

* Host server URL rewrites now propagating correctly.


1.0.1
-----

* Full WSGI support – passes the wsgiref validation tests.

* Iterable request makes reading input data simple.

* Stream implements writelines for optimized sending of chunks of strings.

* Response implements a Stream.writelines proxy, automatically calling
  begin().

* Callable response makes responses simpler. Based on writelines.

* Fixed a bug where smisk_multipart_parse_file would try to fclose a
  uninitialized fd. [11c4ffae718f]


1.0.0
-----

* First stable version
