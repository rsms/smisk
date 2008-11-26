:mod:`smisk.wsgi`
=================================================

.. module:: smisk.wsgi

This module provides a way to use Smisk as a WSGI backend.

Conforms to :pep:`333`

Example::

  def hello_app(env, start_response):
    start_response("200 OK", [])
    return ["Hello, World"]
  from smisk.wsgi import main
  main(hello_app)


.. function:: is_hop_by_hop(header_name)

  Return true if 'header_name' is an HTTP/1.1 "Hop-by-Hop" header


.. function:: main(wsgi_app, appdir=None, bind=None, forks=None, handle_errors=True, cli=True)

  Helper for setting up and running an application.

  This is normally what you do in your top module ``__init__``::

    from smisk.wsgi import main
    from your.app import wsgi_app
    main(wsgi_app)

  Your module is now a runnable program which automatically
  configures and runs your application. There is also a Command Line
  Interface if *cli*  evaluates to ``True``.

  :param wsgi_app:
    A WSGI application
  :param appdir:
    Path to the applications base directory.
  :param bind:
    Bind to address (and port). Note that this overrides
    ``SMISK_BIND``.
  :param forks:
    Number of child processes to spawn.
  :param handle_errors:
    Handle any errors by wrapping calls in
    *handle_errors_wrapper()*
  :param cli:
    Act as a *Command Line Interface*, parsing command line
    arguments and options.
  :rtype:
    None



.. class:: smisk.wsgi.Gateway(smisk.core.Application)

  WSGI adapter
  
  .. method:: __init__(wsgi_app)
  
  .. method:: service()

  .. method:: start_response(status, headers, exc_info=None)

    *start_response()* callable as specified by PEP 333


.. class:: smisk.wsgi.Request(smisk.core.Request)

  WSGI request

  .. method:: prepare(app)

    Set up the environment for one request

  .. method:: send_file(path)

