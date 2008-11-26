:mod:`smisk.config`
=================================================

.. module:: smisk.config
.. versionadded:: 1.1

User configuration.

Arbitrary configuration file utility.

Configuration file syntax
-------------------------------------------------

The configuration syntax is basically a Python script which is ``eval`` ed
into a dict:

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

The configuration file must contain a literal Python dictionary and might 
leave out the wrapping "{" and "}", as demonstrated in the example above.

JavaScript/JSON-style comments are supported:

.. code-block:: javascript
  
  "interval": 12.7, /* A value in the range [0,123)  */
  
  "database": {
    "connection": "mysql://john@foo.bar/grek",
    
    /* Enables automatic reloading of entites: */
    "auto_reload": true
  },


Filters
-------------------------------------------------

TODO


Logging
-------------------------------------------------

TODO

:see: :func:`configure_logging()`


Practical use
-------------------------------------------------

Normally, you use the shared instance :attr:`config`
::

  from smisk.config import config
  config('my-app')
  print config['some_key']

If your system have different default configuration directories, these might 
be added module-wide by modifying :attr:`config_locations`
::

  from smisk.config import config_locations, config
  config_locations[0:0] = ['/etc/spotify/default', '/etc/spotify']
  config('my-app')
  # loading /etc/spotify/my-app.conf
  print config['some_key']

In the case you need separate sets of configuration available in parallel, 
:class:`Configuration` can be used to create new configuration
dictionaries::

  from smisk.config import Configuration
  config1 = Configuration()
  config2 = Configuration()
  config1('my-app1')
  config2('my-app2')
  print config1['some_key']
  print config2['something_else']


Sources
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Every :class:`Configuration` instance contains a list of all sources (string and files) used to create the configuration dictionary. This information is used by :meth:`Configuration.reload()` in order to correctly update and merge options. You can access this list of sources through :attr:`Configuration.sources`
::

  from smisk.config import config
  config('my-app')
  print 'Sources:', config.sources


Symbols
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A set of basic symbols, constructed to simplify syntax, are available through 
:attr:`Configuration.default_symbols`. During call-time, you can also pass an
extra set of symbols, being combined with default_symbols when ``eval`` ing
configurations
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

Predefined symbols:

=========  ================
NAME       VALUE           
=========  ================
true       True            
false      False           
null       None            
CRITICAL   logging.CRITICAL
DEBUG      logging.DEBUG   
ERROR      logging.ERROR   
FATAL      logging.FATAL   
INFO       logging.INFO    
NOTSET     logging.NOTSET  
WARN       logging.WARN    
WARNING    logging.WARNING 
critical   logging.CRITICAL
debug      logging.DEBUG   
error      logging.ERROR   
fatal      logging.FATAL   
info       logging.INFO    
notset     logging.NOTSET  
warn       logging.WARN    
warning    logging.WARNING
=========  ================


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
  from smisk.config import config
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

  from smisk.config import config
  config(os.path.basename(os.environ['SMISK_APP_DIR']))

Contents of my_app/config/devel.py::

  from smisk.config import config
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
  from smisk.config import config
  
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


.. attribute:: LOGGING_FORMAT
  
  Default logging format


.. attribute:: LOGGING_DATEFMT
  
  Default logging date format


.. function:: configure_logging(conf)
  
  Configure the logging module based on *conf* dictionary.
  
  This function is automatically applied by :class:`Configuration` after
  configuration has been loaded and if :attr:`Configuration.logging_key` is set
  (which it is by default).
  
  The *conf* dictionary is sarched for several parameters:
  
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
    call :meth:`Configuration.reload()` afterwards, in order to actually apply
    the defaults. If you simply assign a new dictionary to 
    :attr:`Configuration.defaults`, reloading is done automatically through the
    property set method.
  
  
  .. attribute:: sources

    Ordered list of sources used to create this dict.

    Each entry is a tuple with two items::

      ( string <path or string hash>, dict configuration )

    <path or string hash> is used to know where from and configuration is the 
    unmodified, non-merged configuration this source generated.
  
  
  .. attribute:: filters

    A list of filters which are applied after configuration has been loaded.

    A filter receives the configuration dictionary, possibly as a result of
    several sources merged, and should not return anything::
  
      def my_filter(conf):
        if 'my_special_key' in conf:
          something_happens(conf['my_special_key'])
      config.add_filter(my_filter)
  
    Filters are automatically applied both when initially loading and also when
    reloading configuration.
  
    :see: :meth:`Configuration.add_filter`


  .. attribute:: filename_ext

    Filename extension of configuration files
  
  
  .. attribute:: logging_key
  
    Name of logging key
    
    :default: :samp:`"logging"`
  

  .. method:: __init__(*args, **defaults)
  
    Create a new :class:`Configuration`, optionally 
    setting :attr:`Configuration.defaults`.


  .. method:: __call__(name, locations=[], symbols={}, logging_key=None)
  
    Load configuration files from a series of pre-defined locations.
  
    By default, will look for these files in the following order::

      /etc/default/<name>.conf
      /etc/<name>.conf
      /etc/<name>/<name>.conf
      ./<name>.conf
      ./<name>-user.conf
      ~/<name>.conf


  .. method:: load(path, symbols={}, post_process=True)
  
    Load configuration from file denoted by *path*.


  .. method:: loads(string, symbols={}, post_process=True)
  
    Load configuration from string.


  .. method:: reload()

    Reload all sources, effectively reloading configuration.
  
    You can for example register a signal handler which reloads the
    configuration::

      from smisk.config import config
      import signal
      signal.signal(signal.SIGHUP, lambda signum, frame: config.reload())
      config('my_app')
      import os
      os.kill(os.getpid(), signal.SIGHUP)
      # config.reload() called
  

  .. method:: add_filter(self, filter)

    Add a filter.
  
    :See: :attr:`Configuration.filters`

