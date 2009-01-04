:class:`~smisk.core.Application` --- An application
===========================================================

.. module:: smisk.core

.. class:: smisk.core.Application

  An application.

  Simple example::

   from smisk.core import Application
   class MyApp(Application):
     def service(self):
       self.response.write('<h1>Hello World!</h1>')
 
   MyApp().run()

  Example of standalone/listening/slave process::

   from smisk.core import Application, bind
   class MyApp(Application):
     def service(self):
       self.response.write('<h1>Hello World!</h1>')
  
   bind('hostname:1234')
   MyApp().run()

  It is also possible to use your own types to represent :class:`~smisk.core.Requests` and :class:`~smisk.core.Responses`. You set :attr:`~smisk.core.Application.request_class` and/or :attr:`~smisk.core.Application.response_class` to a type, before :meth:`~smisk.core.Application.application_will_start()` has been called. For example::

   from smisk.core import Application, Request
   class MyRequest(Request):
     def from_internet_explorer(self):
       return self.env.get('HTTP_USER_AGENT','').find('MSIE') != -1
 
   class MyApp(Application):
     def __init__(self):
       super(MyApp, self).__init__()
       self.request_class = MyRequest
 
     def service(self):
       if self.request.from_internet_explorer():
         self.response.write('<h1>Good bye, cruel World!</h1>')
       else:
         self.response.write('<h1>Hello World!</h1>')
 
   MyApp().run()


Class attributes
-------------------------------------------------
.. attribute:: smisk.core.Application.current
  
  Current application instance, if any. Class attribute.
  
  :see: :attr:`smisk.core.app`


Instance attributes
-------------------------------------------------

.. attribute:: smisk.core.Application.forks

  Number of child processes to fork off into.

  This must be set before calling :meth:`~smisk.core.Application.run()`, as
  it's in :meth:`~smisk.core.Application.run()` where the forking goes down.
  Defaults to 0 (disabled).

  .. versionadded:: 1.1

.. attribute:: smisk.core.Application.request_class

  Must be set before calling :meth:`~smisk.core.Application.run()`

.. attribute:: smisk.core.Application.response_class

  Must be set before calling :meth:`~smisk.core.Application.run()`

.. attribute:: smisk.core.Application.sessions_class

  Must be set before calling :meth:`~smisk.core.Application.run()` and should
  be an object implementing the :class:`smisk.session.Store` interface.

.. attribute:: smisk.core.Application.request
  
  The :class:`~smisk.core.Request` object.

.. attribute:: smisk.core.Application.response
  
  The :class:`~smisk.core.Response` object.

.. attribute:: smisk.core.Application.sessions

  An object with the :class:`smisk.session.Store` interface.

.. attribute:: smisk.core.Application.show_traceback
  
  If True, traceback information is included with error responses. Note that
  traceback information is always included in logs. Defaults to True.


Instance methods
-------------------------------------------------

.. method:: smisk.core.Application.application_did_stop()

  Called when the application stops accepting incoming requests.

  The default implementation does nothing.

.. method:: smisk.core.Application.application_will_start()

  Called just before the application starts accepting incoming requests.

  The default implementation does nothing.

.. method:: smisk.core.Application.error(typ, val, tb)

  Handle an error and produce an appropriate response.

  The built-in implementation renders error information as XHTML
  encoded in UTF-8 with the HTTP status code 500 (Internal Server
  Error).

  You might override this to display a custom error response, but
  it is recommended you use this implementation, or at least
  filter certain higher level exceptions and let the lower ones
  through to this handler.

  Normally, this is what you do::

    class MyApp(Application):
      def error(self, typ, val, tb):
       if isinstance(val, MyExceptionType):
        self.nice_error_response(typ, val)
       else:
        Application.error(self, typ, val, tb)

  What is sent as response depends on if output has started or not: If output
  has started, if :attr:`~smisk.core.Response.has_begun` is ``True``, calling
  this method will insert a HTML formatted error message at the end of what
  has already been sent. If output has not yet begun, any headers set will 
  be discarded and a complete HTTP response will be sent, including the same
  HTML message described earlier.

  If :attr:`~smisk.core.Application.show_traceback` evaluates to true, the
  error message will also include a somewhat detailed backtrace. You should
  disable :attr:`~smisk.core.Application.show_traceback` in production
  environments.
  
  :param typ: Exception type
  :param val: Exception value
  :param tb:  Traceback

.. method:: smisk.core.Application.exit()

  Exit application.

.. method:: smisk.core.Application.run()

  Run application.

.. method:: smisk.core.Application.service()

  Service a request.
