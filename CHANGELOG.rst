Changes
=======

1.1.6
-----

* Handle requests with filename extensions which are actually not filename
  extensions but rather format-less but leet.haxxor kinda dot notation of the
  regular path component.

* Fixed 304 Not Modified response status not to set Location header nor include
  a message-body.

* smisk.util.main.daemonize() does no longer call exit hooks while detaching
  (calling os._exit instead of sys.exit in dead forks).

* Fixed bug in smisk.util.main.control_process_runloop() where signals where
  not correctly forwarded to children.

* When core fail to decode text data from user input (form data and query 
  string) it will try to decode the text data using a fallback charset, defined
  by SMISK_FALLBACK_CHARSET in config.h, which is set to "ISO-8859-1" in
  accordance with HTTP 1.1 (RFC 2616), sect. 19.3 "Tolerant Applications".

* MVC applications respond with "400 Bad Request" when user input text can not
  be decoded using app.charset (or iso-8859-1 if app.tolerant is True).

* core.Application has a new boolean property "tolerant". When True (default)
  user input will be processed in a tolerant manner. I.e. if a query string
  encoded in iso-8859-1 is sent to an application with app.charset of utf-8,
  the query string will still be decoded using the HTTP 1.1 (RFC 2616) fallback
  encoding iso-8859-1, which is able do decode any byte. If tolerant where 
  False, a UnicodeDecodeError would be raised.

* Static method core.URL.decompose_query() accepts a new boolean argument 
  "tolerant" which if True, charset argument is set and can not be used to 
  decode the first argument, causes decoding using the iso-8859-1 charset.

* mvc.Response have two new members: The property "charsets" which is a list of
  acceptable charsets. The method "accepts_charset" which return True if the 
  first argument is acceptable according to the "charsets" list.

1.1.5
-----

* Fixed a bug with Python 2.5 where PyEval_InitThreads had to be called (even
  though the documentation suggests otherwise)

1.1.4
-----

* Fixed serious integer overflow bugs in smisk.core where return values from
  PyObject_CallMethod was never decrefed, leading to incorrect number of 
  decrefs later on thus causing seemingly random segfaults. Thanks to Ludde.

* Removed the bsddb module -- the smisk.ipc.bsddb module still exist, but
  required an external bsddb module to be installed.

* Fixed a bug in smisk.ipc.memcached where creation of dict cash key tried to
  concatenate a str and int.

* Fixed a bug in smisk.mvc request parsing code where a text payload with an
  explicit character encoding was not properly handled.

* The smisk.serialization.json module now uses the standard library
  (Python >=2.6) json module when cjson is not available.

* The smisk.serialization.json serializer explicitly specifies the character
  encoding (which always is UTF-8)

* The smisk.serialization.php_serial serializer now uses "sphp" as the primary
  filename extension. (updated to align with evolving standards)

* Fixed some issues with storage defined in both header file and source file,
  leading to problems with compilation of Python 2.4 version of smisk.core.

* Higher performance codec in smisk.core.xml now also supporting
  decoding/unescaping.


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

* smisk.core.Request have two soft limits -- max_multipart_size and 
  max_formdata_size -- for limiting automatically handled input data size. These
  soft limits can also be used to disable the automated parsing of Smisk.

* smisk.util.cache has a new function -- app_shared_key -- returning a byte
  string which can be used to uniqely identify the application. The key is
  based on the entry file (the python file in which __name__ == "__main__").

* smisk.util.type exposes MutableMapping -- in Python >=2.6 this is 
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

* MVC module -- smisk.mvc.

* Better unicode support.

* Compatible with Debian Etch.

* Host server URL rewrites now propagating correctly.


1.0.1
-----

* Full WSGI support -- passes the wsgiref validation tests.

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
