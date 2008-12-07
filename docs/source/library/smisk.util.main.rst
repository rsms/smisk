:mod:`smisk.util.main`
===========================================================

.. module:: smisk.util.main
.. versionadded:: 1.1


Configuration parameters
-------------------------------------------------

.. describe:: smisk.emergency_logfile

  In case an application running with help from :func:`handle_errors_wrapper` (if running using :func:`main` with *handle_errors=True*) raises an exception outside of serving a HTTP transaction, Smisk will write (append) backtrace and error info to this file.
  
  If not specified, the following path is used:
  
  #. env["SMISK_LOG_DIR"] + "/error.log" if *SMISK_LOG_DIR* is set in environ (not set by default)
  #. env["SMISK_APP_DIR"] + "/error.log" if *SMISK_APP_DIR* is set in environ (by default, smisk tries to deduce and set this if not already set)
  #. "./error.log" as a last resort, if neigher *smisk.emergency_logfile*, *SMISK_LOG_DIR* or *SMISK_APP_DIR* is present.
  
  :type: string
  :default: :samp:`None`


Module contents
-------------------------------------------------


.. function:: absapp(application, default_app_type=smisk.core.Application, *args, **kwargs)

  Returns an application instance.
  
  *application* can be None, a subclass of :class:`smisk.core.Application` or an instance of some kind of :class:`smisk.core.Application`.
  
  * If *application* is ``None``...
    * ...and there is already a global application instance, :attr:`smisk.core.Application.current` is returned.
    * ...and there is no global application instance, a new instance of *default_app_type* is created. ``*args`` and ``**kwargs`` are passed to the constructor.
  * If *application* is a subclass of :class:`smisk.core.Application`, an instance of that type will be created. ``*args`` and ``**kwargs`` are passed to the constructor.
  * If *application* is already an instance of some kind of :class:`smisk.core.Application`, *application* is returned untouched.
  
  :raises ValueError: if not possible.
  :rtype: :class:`smisk.core.Application`


.. function:: setup_appdir(appdir=None)
  
  Assures the ``SMISK_APP_DIR`` environment variable is set and points to the application directory.
  
  If *appdir* is None, this function uses the following strategy for guessing the application directory::
  
    appdir = os.path.dirname(sys.modules['__main__'].__file__)


.. function:: main_cli_filter(appdir=None, bind=None, forks=None)

  Command Line Interface parser.
  
  For instance, it's used by :func:`smisk.mvc.main()`.
  
  **Command line arguments:**
  
  .. cmdoption:: --appdir PATH, --bind ADDR, --debug, --forks N, --help
    
    When running as a program.


.. function:: handle_errors_wrapper(fnc, error_cb=sys.exit, abort_cb=None, *args, **kwargs)

  Call *fnc* catching any errors and writing information to ``error.log``.
  
  ``error.log`` will be written to, or appended to if it aldready exists,
  ``ENV["SMISK_LOG_DIR"]/error.log``. If ``SMISK_LOG_DIR`` is not set,
  the file will be written to ``ENV["SMISK_APP_DIR"]/error.log``.
  As a last resort ``./error.log`` is used, in the case ``ENV["SMISK_APP_DIR"]``
  is not present.
  
  * ``KeyboardInterrupt`` is discarded/passed, causing a call to `abort_cb`,
    if set, without any arguments.
  
  * ``SystemExit`` is passed on to Python and in normal cases causes a program
    termination, thus this function will not return.
  
  * Any other exception causes ``error.log`` to be written to and finally
    a call to `error_cb` with a single argument; exit status code.
  
  .. envvar:: SMISK_LOG_DIR
  
    Custom directory in which to write the error.log file.
  
  :param  error_cb:   Called after an exception was caught and info 
                               has been written to ``error.log``. Receives a
                               single argument: Status code as an integer.
                               Defaults to ``sys.exit`` causing normal program
                               termination. The returned value of this callable
                               will be returned by `handle_errors_wrapper` itself.
  :type   error_cb:   callable
  :param  abort_cb:   Like *error_cb* but instead called when
                      ``KeyboardInterrupt`` was raised.
  :type   abort_cb:   callable
  :rtype: object


.. function:: main(application=None, appdir=None, bind=None, forks=None, handle_errors=True, cli=True, config=None, *args, **kwargs) -> object

  Helper for setting up and running an application.

  This function handles command line options, calls :meth:`Application.setup()` to set
  up the application, and then calls :meth:`Application.run()`, entering the runloop.

  This is normally what you do in your top module *__init__*::
  
    from smisk.mvc import main
    if __name__ == '__main__':
      main()

  Your module is now a runnable program which automatically
  configures and runs your application.

  Excessive arguments and keyword arguments are passed to
  :meth:`Application.__init__()`. If *application* is already an
  instance, these extra arguments and keyword arguments have no
  effect.
  
  This function is not a true function, but rather an instance of :class:`Main`.

  :param application:
    An application type or instance.
  :param appdir:
    Path to the applications base directory.
  :param bind:
    Bind to address (and port). Note that this overrides ``SMISK_BIND``.
  :param forks:
    Number of child processes to spawn.
  :param handle_errors:
    Handle any errors by wrapping calls in :func:`smisk.util.main.handle_errors_wrapper()`
  :param cli:
    Act as a *Command Line Interface*, parsing command line arguments and options.
  :Returns:
    Anything returned by :meth:`Main.run()`
  :See:
    :meth:`Main.setup()`, :meth:`Main.run()`


Classes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


.. class:: Main(object)

  Normally used through the common instance :func:`main()`.

  .. attribute:: default_app_type
  
  
  .. method:: __call__(application=None, appdir=None, bind=None, forks=None, handle_errors=True, cli=True, *args, **kwargs)
  
    Helper for setting up and running an application.
    
    See documentation of :func:`main()`
    
  
  .. method:: setup(self, application=None, appdir=None, *args, **kwargs)
    
    Helper for setting up an application.

    ``*args`` and ``**kwargs`` are passed to :func:`absapp()`

    This function can only be called once. Successive calls simply
    returns the current application without making any modifications.
    If you want to update the application state, see
    *Application.setup()* instead, which can be called multiple times.

    .. describe:: appdir
    
      The application directory is the physical path in which your
      application module resides in the file system. Smisk need to know
      this and tries to automatically figure it out. However, there are
      cases where you need to explicitly define your application
      directory. For instance, if you'r calling *main()* or *setup()*
      from a sub-module of your application.

      There are currently two ways of manually setting the application
      directory:

      1. If *appdir* **is** specified, the environment variable
         ``SMISK_APP_DIR`` will be set to it's value, effectively
         overwriting any previous value.

      2. If *appdir* is **not** specified the application directory path
         will be aquired by :samp:`dirname(<__main__ module>.__file__)`.

    **Environment variables**
  
    .. envvar:: SMISK_APP_DIR
  
      The physical location of the application. If not set, the value
      will be calculated like ``abspath(appdir)`` if the *appdir*
      argument is not None. In the case *appdir* is None, the value
      is calculated like this: :samp:`dirname(<__main__ module>.__file__)`.

    .. envvar:: SMISK_ENVIRONMENT
  
      Name of the current environment. If not set, this will be set to
      the  default value returned by 'environment()'.
  
    :param application:
      An application type or instance.
    :param appdir:
      Path to the applications base directory. Setting this will
      overwrite any previous value of environment variable
      ``SMISK_APP_DIR``.
    :Returns:
      The application
    :rtype:
      :class:`Application`
    :See:
      :func:`main()`, :func:`absapp()`, :func:`setup_appdir()`, :meth:`run()`
  
  
  .. method:: run(self, bind=None, application=None, forks=None, handle_errors=False)
    
    Helper for running an application.

    Note that because of the nature of ``libfcgi`` an application can
    not be started, stopped and then started again. That said, you can
    only start  your application once per process. (Details:
    OS_ShutdownPending sets a process-wide flag causing any call to
    accept to bail out)
    
    **Environment variables**

    .. envvar:: SMISK_BIND
  
      If set and not empty, a call to ``smisk.core.bind`` will occur,
      passing the value to bind, effectively starting a stand-alone
      process.
  
    :param bind:
      Bind to address (and port). Note that this overrides ``SMISK_BIND``.
    :param application:
      An application type or instance.
    :param forks:
      Number of child processes to spawn.
    :param handle_errors:
      Handle any errors by wrapping calls in :func:`smisk.util.main.handle_errors_wrapper()`
    :Returns:
      Anything returned by *application.run()*
    :rtype:
      object
    :See:
      :func:`main()`, :meth:`setup()`


