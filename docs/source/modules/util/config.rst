:mod:`smisk.util.config`
=================================================

.. versionadded:: 1.1

User configuration.

Arbitrary configuration file utility.

Configuration file syntax
-------------------------------------------------

The configuration syntax is basically a Python script which is ``eval`` ed
into a dict::

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
    "": WARN,
    "some.module": DEBUG
  }

The configuration file must contain a literal Python dictionary and might 
leave out the wrapping "{" and "}", as demonstrated in the example above.

Two kinds of comments are supported:

  * Python-style "dash" (lines beginning with ``#``)
  * JavaScript/JSON-style ``/*...*/``

Example of embedded comments::

  "interval": 12.7, /* A value in the range [0,123)  */
  
  "database": {
    "connection": "mysql://john@foo.bar/grek",
    
    # Enables automatic reloading of entites
    "auto_reload": true
  },


Practical use
-------------------------------------------------

Normally, you use the shared instance :attr:`config`::

  from smisk.util.config import config
  config('my-app')
  print config['some_key']

If your system have different default configuration directories, these might 
be added module-wide by modifying :attr:`config_locations`::

  from smisk.util.config import config_locations, config
  config_locations[0:0] = ['/etc/spotify/default', '/etc/spotify']
  config('my-app')
  # loading /etc/spotify/my-app.conf
  print config['some_key']

In the case you need separate sets of configuration available in parallel, 
:class:`Configuration` can be used to create new configuration dictionaries::

  from smisk.util.config import Configuration
  config1 = Configuration()
  config2 = Configuration()
  config1('my-app1')
  config2('my-app2')
  print config1['some_key']
  print config2['something_else']


Sources
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Every :class:`Configuration` instance contains a list of all soruces (string 
and files) used to create the configuration dictionary. This information is 
used by :meth:`Configuration.reload()` in order to correctly update and merge 
options. You can access this list of sources through 
:attr:`Configuration.sources`::

  from smisk.util.config import config
  config('my-app')
  print 'Sources:', config.sources


Symbols
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A set of basic symbols, constructed to simplify syntax, are available through 
:attr:`Configuration.default_symbols`. During call-time, you can also pass an
extra set of symbols, being combined with default_symbols when ``eval`` ing
configurations::

  from smisk.util.config import config
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

Predefined symbols::

  NAME      VALUE
  --------- ----------------
  true      True
  false     False
  yes       True
  no        False
  null      None
  CRITICAL  logging.CRITICAL
  DEBUG     logging.DEBUG
  ERROR     logging.ERROR
  FATAL     logging.FATAL
  INFO      logging.INFO
  NOTSET    logging.NOTSET
  WARN      logging.WARN
  WARNING   logging.WARNING
  critical  logging.CRITICAL
  debug     logging.DEBUG
  error     logging.ERROR
  fatal     logging.FATAL
  info      logging.INFO
  notset    logging.NOTSET
  warn      logging.WARN
  warning   logging.WARNING


Smisk MVC applications
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In a typical Smisk MVC application, you have a config module directly inside
your application module::

  my_app/
    __init__.py
    config.py

Inside config.py (or config/__init__.py, depending on your setup) you load a
configuration of choice::

  # config.py
  from smisk.util.config import config
  config(os.path.basename(os.environ['SMISK_APP_DIR']))

Considering the previous example directory layout, this will try to load
configuration files named 'my_app'.

As Smisk supports the notion of an "environment" and also loads multiple 
application config modules if available, it's possible to load, or override, 
configurations with little effort. Let's use another example directory layout,
with multiple application config modules::

  my_app/
    __init__.py
    config/
      __init__.py
      devel.py

Contents of my_app/config/__init__.py::

  from smisk.util.config import config
  config(os.path.basename(os.environ['SMISK_APP_DIR']))

Contents of my_app/config/devel.py::

  from smisk.util.config import config
  config(os.path.basename(os.environ['SMISK_APP_DIR']) + '-devel')

Now when the application starts with SMISK_ENVIRONMENT set to "devel":

  * my_app/config/__init__.py is first executed, loading the basic set of 
    configuration from one or many files.
  
  * my_app/config/devel.py is then executed, overloading parts of or all
    previous configuration.


Smisk core applications
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There is no such thing as a typical Smisk core application, but let's assume
a very simple hello world implementation, returning the value of a
configuration key called "message"::

  from smisk.core import Application
  from smisk.util.config import config
  
  class MyApp(Application):
    def __init__(self):
      Application.__init__(self)
      config('my_app')
    
    def service(self):
      self.response('message: ', config.get('message', 'No message configured'))
  
  if __name__ == '__main__':
    MyApp().run()


Module contents
-------------------------------------------------


.. attribute:: config

  Shared :class:`Configuration`.


.. attribute:: config_locations
  
  List of default directories in which to look for configurations files,
  effective when using :meth:`Configuration.__call__()`.


.. class:: Configuration(dict)
  
  Configuration dictionary.
  
  Example use::
  
    from smisk.util.config import Configuration
    cfg = Configuration()
    cfg('my-app')
    print cfg['some_key']
  
  
.. attribute:: Configuration.defaults

  Default values.
  
  If you modify this dict after any configuration has been loaded, you need to
  call :meth:`Configuration.reload()` afterwards, in order to actually apply
  the defaults. If you simply assign a new dictionary to 
  :attr:`Configuration.defaults`, reloading is done automatically through the
  property set method.
  
  
.. attribute:: Configuration.sources

  Ordered list of sources used to create this dict.

  Each entry is a tuple with two items::

    ( string <path or string hash>, dict configuration )

  <path or string hash> is used to know where from and configuration is the 
  unmodified, non-merged configuration this source generated.


.. method:: Configuration.__init__(self, *args, **defaults)
  
  Create a new `Configuration`, optionally setting `defaults`.


.. method:: Configuration.__call__(self, name, locations=[], symbols={}, logging_key='logging', fext='.conf')
  
  Load configuration files from a series of pre-defined locations.
  
  By default, will look for these files in the following order::

    /etc/default/<name>.conf
    /etc/<name>.conf
    /etc/<name>/<name>.conf
    ./<name>.conf
    ./<name>-user.conf
    ~/<name>.conf


.. method:: Configuration.load_file(self, path, symbols={})
  
  Load configuration from file denoted by `path`.


.. method:: Configuration.loads(self, string, symbols={})
  
  Load configuration from string.


.. method:: Configuration.reload(self)

  Reload all sources, effectively reloading configuration.
  
  You can for example register a signal handler which reloads the
  configuration::

    from smisk.util.config import config
    import signal
    signal.signal(signal.SIGHUP, lambda signum, frame: config.reload())
    config('my_app')
    import os
    os.kill(os.getpid(), signal.SIGHUP)
    # config.reload() called


.. method:: Configuration.setup_logging(self, key='logging')
  
  Setup logging using dictionary keyed with `key`.

