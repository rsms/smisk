:mod:`smisk.config`
=================================================

.. module:: smisk.config
.. versionadded:: 1.1

User configuration.

Arbitrary configuration file utility.

Configuration file syntax
-------------------------------------------------

The configuration syntax is `JSON <http://www.ietf.org/rfc/rfc4627.txt>`__-compliant
and should represent a dictionary:

.. code-block:: javascript

  "interval": 12.7,
  "database": {
    "connection": "mysql://john@foo.bar/grek",
    "auto_reload": true
  },
  "sockets": [
    "tcp://127.0.0.1:1234",
    "tcp://127.0.0.1:1235",
    "tcp://127.0.0.1:1236"
  ],
  "logging": {
    "levels": {
      "": WARN,
      "some.module": DEBUG
    }
  }

The configuration file must contain a literal JSON dictionary and might 
leave out the outer curly brackets (``{`` and ``}``), as demonstrated in
the example above.

JavaScript/JSON-style comments are supported:

.. code-block:: javascript
  
  "interval": 12.7, /* A value in the range [0,123)  */
  
  "database": {
    "connection": "mysql://john@foo.bar/grek",
    
    /* Enables automatic reloading of entites: */
    "auto_reload": true
  },


Includes
-------------------------------------------------

Files can be included using the special key ``@include``

.. code-block:: javascript
  
  "interval": 12.7, /* A value in the range [0,123) */
  "@include": "another/file.conf",

Multiple files can be included at once by specifying a list of paths:

.. code-block:: javascript
  
  "interval": 12.7, /* A value in the range [0,123) */
  "@include": ["another/file.conf", "/yet/another/file.conf"],

Paths can be expanded using `glob <http://docs.python.org/library/glob.html>`__, so another way of including multiple file is using a `glob pattern <http://docs.python.org/library/fnmatch.html>`__:

.. code-block:: javascript
  
  "interval": 12.7, /* A value in the range [0,123) */
  "@include": "conf.d/*.conf",

Glob patterns can be included in lists too:

.. code-block:: javascript
  
  "interval": 12.7, /* A value in the range [0,123) */
  "@include": ["conf.d/*.conf", "other/*/*.conf"],

Paths deduced from a glob pattern are loaded in ascending alphabetical order. This enables variable configuration directories, like those of Apache HTTPd and LigHTTPd. Consider the following file layout::

  some-path/
    my-app.conf
    conf.d/
      001-users.conf
      002-database.conf
      321-extras.conf

Now consider *my-app.conf* to contain the following configuration:

.. code-block:: javascript
  
  "interval": 12.7, /* A value in the range [0,123) */
  "@include": "conf.d/*.conf",

It's fully predictable what happens:

#. *my-app.conf* is loaded and applied

#. *001-users.conf* is loaded and applied

#. *002-users.conf* is loaded and applied

#. *321-users.conf* is loaded and applied

In other words, files included (using ``@include``) overrides the parent configuration. --- Or: --- Files inheriting another file is based on the other file.

.. note::
  
  Relative paths are always relative to the file which is defining them. If file */foo/bar.conf* defines ``"@include": "more/abc.conf"``, */foo/more/abc.conf* is loaded. If */foo/more/abc.conf* defines ``"@include": "more/xyz.conf"``, */foo/more/more/xyz.conf* is loaded.


@inherit
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Another including directive, or special key, is ``@inherit``, which work much like ``@include``, with the difference in what gets applied first (what configuration might override the other).

Let's consider the previous example, but instead using the ``@inherit`` directive:

.. code-block:: javascript
  
  "@inherit": "conf.d/*.conf",
  "interval": 12.7, /* A value in the range [0,123)  */

This is the order in which files are loaded and applied:

#. *my-app.conf* is loaded

#. *001-users.conf* is loaded and applied

#. *002-users.conf* is loaded and applied

#. *321-users.conf* is loaded and applied
   
#. *my-app.conf* is applied

In other words, files inherited (using ``@inherit``) is overridden by the parent configuration.

Note that ``@inherit`` is *not* the inverse or reverse of ``@include``, but rather a hybrid of a reverse ``@include`` and a normal ``@include``.

``@inherit`` is comparable to class inheritance in Python.


Logging
-------------------------------------------------

Logging (the standard library `logging <http://docs.python.org/library/logging.html>`__ module)
can be configured based on a dictionary passed to :func:`configure_logging()`:

.. code-block:: javascript

  {
    'stream': 'stdout',
    'filename': '/var/log/myapp.log',
    'filemode', 'a',
    'format': '%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
    'datefmt': '%H:%M:%S',
    'levels': {
      '': WARN,
      'some.module': DEBUG
    }
  }

.. describe:: stream
  
  If present, the root logger will be configured with a
  `StreamHandler <http://docs.python.org/library/logging.html#logging.StreamHandler>`__,
  writing to stream :samp:`sys.{stream}`.
  
  Two streams are available:
  
  * stdout --- Standard output
  * stderr --- Standard error
  
  This parameters is shadowed by the *filename* parameter. Only one of *filename*
  and *stream* should be present in the configuration.

.. describe:: filename, filemode
  
  If present, the root logger will be configured with a
  `FileHandler <http://docs.python.org/library/logging.html#logging.FileHandler>`__,
  writing to the file denoted by *filename*, using mode *filemode* (or "a" if 
  *filemode* is not set).
  
  This parameters takes precedence over the *stream* parameter.

.. describe:: format, datefmt

  If present, the handler of the root logger will be configured to use a
  `Formatter <http://docs.python.org/library/logging.html#logging.Formatter>`__
  based on this format.

.. describe:: levels

  A dictionary with logging levels keyed by logger name.
  
  Note that the root logger level is set by associating a level with the empty string. I.e.:
  
  .. code-block:: javascript
    
    'levels': {
      '': WARN,
    }

.. note::

  Logging is automatically configured by :class:`Configuration` after some
  configuration has been loaded (if :attr:`Configuration.logging_key` is
  exists in the loaded configuration).

:see: :func:`configure_logging()`
:see: :attr:`Configuration.logging_key`


Symbols
-------------------------------------------------

A set of basic symbols, meant to simplify syntax (and to make configuration
files compatible with Python repr), are available through 
:attr:`Configuration.default_symbols`. During call-time, you can also pass an
extra set of symbols, being combined with and overriding default_symbols when
``eval`` ing configurations.
::

  from smisk.config import config
  config.default_symbols['foo'] = 'Foo!'
  config.loads('"some_key": foo')
  print config['some_key']
  # Foo!
  config.loads('"some_key": foo', symbols={'foo':'BAR'})
  print config['some_key']
  # BAR
  config.loads('"some_key": foo')
  print config['some_key']
  # Foo!


Predefined symbols
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

=========  ================
Symbol     Python value
=========  ================
true       True
false      False
null       None
CRITICAL   logging.CRITICAL
FATAL      logging.FATAL
ERROR      logging.ERROR
WARN       logging.WARN
WARNING    logging.WARNING
INFO       logging.INFO
DEBUG      logging.DEBUG
NOTSET     logging.NOTSET
critical   logging.CRITICAL
fatal      logging.FATAL
error      logging.ERROR
warn       logging.WARN
warning    logging.WARNING
info       logging.INFO
debug      logging.DEBUG
notset     logging.NOTSET
=========  ================


Practical use
-------------------------------------------------

Normally, you use the shared instance :attr:`config`
::

  from smisk.config import config
  config('my-app')
  print config['some_key']

If your system have different default configuration directories than the
default ones, these might be added module-wide by modifying :attr:`config_locations`
::

  from smisk.config import config_locations, config
  config_locations[0:0] = ['/etc/spotify/default', '/etc/spotify']
  config('my-app')
  # loading /etc/spotify/my-app.conf
  print config['some_key']

In the case you need several sets of configurations in parallel, 
:class:`Configuration` can be used to create new configuration
dictionaries::

  from smisk.config import Configuration
  config1 = Configuration(some_key='default value')
  config2 = Configuration()
  config1('my-app1')
  config2('my-app2')
  print config1['some_key']
  print config2['something_else']


Module contents
-------------------------------------------------


.. attribute:: config

  Shared :class:`Configuration`.


.. attribute:: config_locations
  
  List of default directories in which to look for configurations files,
  effective when using :meth:`Configuration.__call__()`.


.. attribute:: LOGGING_FORMAT
  
  Default logging format


.. attribute:: LOGGING_DATEFMT
  
  Default logging date format


.. function:: configure_logging(conf)
  
  Configure the logging module based on *conf* dictionary.
  
  This function is automatically applied by :class:`Configuration` after
  configuration has been loaded and if :attr:`Configuration.logging_key` is set
  (which it is by default).
  
  :see: `Logging`_


.. class:: Configuration(dict)
  
  Configuration dictionary.
  
  Example use::
  
    from smisk.config import Configuration
    cfg = Configuration()
    cfg('my-app')
    print cfg['some_key']
  

  .. attribute:: defaults

    Default values.
  
    If you modify this dict after any configuration has been loaded, you need to
    call :meth:`reload()` afterwards, in order to actually apply
    the defaults.
    
    To set or update single, specific default values, considering using
    :meth:`set_default()` instead, or simply assign a new dictionary to
    :attr:`defaults`. That way reloading is done automatically for you.
    
    :default: :samp:`{}`
  

  .. attribute:: default_symbols

    Default symbols.
    
    :see: `Symbols`_
  
  
  .. attribute:: sources

    Ordered list of sources used to create this dict.

    Each entry is a tuple with two items::

      ( string <path or string hash>, dict configuration )

    *<path or string hash>* is used to know where from and configuration is the 
    unmodified, non-merged configuration this source generated.
    
    Every :class:`Configuration` instance contains a list of all sources
    (string and files) used to create the configuration dictionary. This 
    information is used by :meth:`Configuration.reload()` in order to correctly
    update and merge options.
    ::

      from smisk.config import config
      config('my-app')
      print 'Sources:', config.sources
    
    :default: :samp:`[]`
  
  
  .. attribute:: filters

    List of filters which are applied after configuration has been loaded.

    A filter receives the :class:`Configuration` instance calling it and
    should not return anything::
  
      def my_filter(conf):
        if 'my_special_key' in conf:
          something_happens(conf['my_special_key'])
      config.add_filter(my_filter)
  
    Filters are automatically applied both when initially loading and
    reloading configuration.
    
    :default: :samp:`[]`
    :see: :meth:`add_filter`


  .. attribute:: filename_ext

    Filename extension of configuration files
    
    :default: :samp:`".conf"`
  
  
  .. attribute:: logging_key
  
    Name of logging key
    
    :default: :samp:`"logging"`
    :see: `Logging`_
  
  
  .. attribute:: input_encoding
  
    Character encoding used for reading configuration files.
  
    :default: :samp:`"utf-8"`
  
  
  .. attribute:: max_include_depth
  
    How deep to search for (and load) files denoted by a "@include".
  
    A value of ``0`` or lower disables includes.
    
    :default: :samp:`7`
  

  .. method:: __init__(*args, **defaults)
  
    Create a new :class:`Configuration`, optionally 
    setting :attr:`defaults`.


  .. method:: __call__(name, defaults=None, locations=[], symbols={}, logging_key=None)
  
    Load configuration files from a series of pre-defined locations.
    
    *defaults* is added to (and might override) :attr:`defaults`
  
    By default, will look for these files in the following order::

      /etc/default/<name>.conf
      /etc/<name>.conf
      /etc/<name>/<name>.conf
      ./<name>.conf
      ./<name>-user.conf
      ~/<name>.conf
  
  
  .. method:: set_default(self, key, value)
    
    Assign a default *value* to *key*.


  .. method:: load(path, symbols={}, post_process=True) -> dict
  
    Load configuration from file denoted by *path*.
    
    Returns the configuration loaded from *path*.


  .. method:: loads(string, symbols={}, post_process=True) -> dict
  
    Load configuration from string.
    
    Returns the configuration loaded from *string*.


  .. method:: reload()

    Reload all sources, effectively reloading configuration.
  
    You can for example register a signal handler which reloads the
    configuration:

    ::
    
      from smisk.config import config
      import signal
      signal.signal(signal.SIGHUP, lambda signum, frame: config.reload())
      config('my_app')
      import os
      os.kill(os.getpid(), signal.SIGHUP)
      # config.reload() called
  
  
  .. method:: reset(reset_defaults=True)
    
    Reset this configuration dictionary.
    
    Causes :attr:`sources`, :attr:`filters` and possibly :attr:`defaults` to
    be cleared as well as the configuration dictionary itself.
    

  .. method:: add_filter(self, filter)

    Add a *filter*.
  
    :See: :attr:`filters`

