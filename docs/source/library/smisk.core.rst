core
===========================================================

This module is the foundation of Smisk and is implemented in machine native code.

See :ref:`c-api` for documentation of the C interface.

.. module:: smisk.core
  :synopsis: Handles I/O, HTTP transactions, sessions, etc.

:Requires: `libfcgi <http://www.fastcgi.com/>`_


.. moduleauthor:: Rasmus Andersson <rasmus@flajm.com>


Attributes
-------------------------------------------------

.. attribute:: __build__
  
  Build identifier in URN form, distinguishing each unique build.
  
  :see: :attr:`smisk.release.build` for more information about this attribute.
  
  .. versionchanged:: 1.1.0
    Prior to version 1.1.0, this was a abritrary (per-build unique) string. In 1.1.0 this is now a URN.


.. attribute:: app
  
  Current :class:`Application` (``None`` if no application has been created).
  
  This is actually a :class:`smisk.util.objectproxy.ObjectProxy`, inducing a
  slight performance hit, since accessing the actual application causes
  intermediate calls. :attr:`Application.current` is the most
  performance-effective way to access the current application. However, in most
  cases the performance hit induced by the ObjectProxy is so small, the
  increased readability and usage of app is preferred.
  
  Example::
  
    >>> import smisk
    >>> smisk.app
    None
    >>> import smisk.core
    >>> smisk.core.Application()
    <smisk.core.Application object at 0x6a5c0>
    >>> smisk.app
    <smisk.core.Application object at 0x6a5c0>
  
  :See: :attr:`Application.current`

  .. versionadded:: 1.1.0


.. attribute:: request
  
  Current :class:`Request` (``None`` if no application is running).
  
  This is actually a :class:`smisk.util.objectproxy.ObjectProxy`, inducing a
  slight performance hit, since accessing the actual application causes
  intermediate calls. :attr:`Application.current.request` is the
  most performance-effective way to access the current request. However, in
  most cases the performance hit induced by the ObjectProxy is so small, the
  increased readability of request is preferred.
  
  :See: :attr:`Application.request`

  .. versionadded:: 1.1.0


.. attribute:: response
  
  Current :class:`Response` (``None`` if no application is running).
  
  This is actually a :class:`smisk.util.objectproxy.ObjectProxy`, inducing a
  slight performance hit, since accessing the actual application causes
  intermediate calls. :attr:`Application.current.response` is the 
  most performance-effective way to access the current response. However, in
  most cases the performance hit induced by the ObjectProxy is so small, the
  increased readability of response is preferred.
  
  :See: :attr:`Application.response`

  .. versionadded:: 1.1.0


Functions
-------------------------------------------------

.. function:: bind(path[, backlog=-1])
  
  Bind to a specific unix socket or host (and/or port).
  
  :param path: The Unix domain socket (named pipe for WinNT), hostname, 
               hostname and port or just a colon followed by a port number. 
               e.g. ``"/tmp/fastcgi/mysocket"``, ``"some.host:5000"``, 
               ``":5000"``, ``"\*:5000"``.
  :type  path: string
  :param backlog: The listen queue depth used in the :func:'listen()' call. Set 
                  to negative or zero to let the system decide (recommended).
  :type  backlog: int
  :raises: `smisk.IOError` If already bound.
  :raises: `IOError` If socket creation fails.
  :see: :func:`unbind()`, :func:`listening()`


.. function:: unbind()
  
  Unbind from a previous call to :func:`bind()`.
  
  If not bound, calling this function has no effect. You can test wherethere or
  not the current process is bound by calling :func:`listening()`.
  
  :raises: IOError on failure.

  .. versionadded:: 1.1.0


.. function:: listening() -> string
  
  Find out if this process is a "remote" process, bound to a socket by means of 
  calling :func:`bind()`. If it is listening, this function returns the address and 
  port or the UNIX socket path.
  
  See also: :func:`unbind()`
  
  :raises: smisk.IOError On failure.
  :returns: Bound path/address or None if not bound.


.. function:: uid(nbits[, node=None]) -> string
  
  Generate a universally Unique Identifier.
  
  See documentation of :func:`pack()` for an overview of :func:``nbits``.
  
  The UID is calculated like this::
    
    sha1 ( time.secs, time.usecs, pid, random[, node] )
  
  :Note:  This is *not* a UUID (ISO/IEC 11578:1996) implementation. However it uses 
          an algorithm very similar to UUID v5 (:rfc:`4122`). Most notably, the format 
          of the output is more compact than that of UUID v5.
  
  :param nbits: Number of bits to pack into each byte when creating the string 
                representation. A value in the range 4-6 or 0 in which case 20
                raw bytes are returned. Defaults is 5.
  :type  nbits: int
  :param node:  Optional data to be used when creating the uid.
  :type  node:  string

  .. versionadded:: 1.1.0


.. function:: pack(data[, nbits=5]) -> string

  Pack arbitrary bytes into a printable ASCII string.
  
  **Overview of nbits:**
  
  0 bits, No packing:
    20 bytes ``"0x00-0xff"``
  4 bits, Base 16:
    40 bytes ``"0-9a-f"``
  5 bits, Base 32:
    32 bytes ``"0-9a-v"``
  6 bits, Base 64:
    27 bytes ``"0-9a-zA-Z,-"``
  
  :param data:
  :type  data:  string
  :param nbits: Number of bits to pack into each byte when creating the string 
                representation. A value in the range 4-6.
  :type  nbits: int
  :see: :func:`uid()`

  .. versionadded:: 1.1.0


.. function:: object_hash(object) -> long

  Calculate a hash from any python object.

  .. versionadded:: 1.1.0


Classes
-------------------------------------------------


* :class:`Application`
* :class:`Request`
* :class:`Response`
* :class:`Stream`
* :class:`SessionStore`
* :class:`FileSessionStore`
* :class:`URL`


.. --------------------------------------------------------------------------------------------------------


.. class:: Application

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

  It is also possible to use your own types to represent :class:`~smisk.core.Requests` and :class:`~smisk.core.Responses`. You set :attr:`request_class` and/or :attr:`response_class` to a type, before :meth:`application_will_start()` has been called. For example::

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


  .. attribute:: current
  
    Current application instance, if any. Class attribute.
  
    :see: :attr:`smisk.core.app`


  .. attribute:: forks

    Number of child processes to fork off into.

    This must be set before calling :meth:`run()`, as
    it's in :meth:`run()` where the forking goes down.
    Defaults to 0 (disabled).

    .. versionadded:: 1.1.0

  .. attribute:: request_class

    Must be set before calling :meth:`run()`

  .. attribute:: response_class

    Must be set before calling :meth:`run()`

  .. attribute:: sessions_class

    Must be set before calling :meth:`run()` and should
    be an object implementing the :class:`smisk.session.Store` interface.

  .. attribute:: request
  
    The :class:`~smisk.core.Request` object.

  .. attribute:: response
  
    The :class:`~smisk.core.Response` object.

  .. attribute:: sessions

    An object with the :class:`smisk.session.Store` interface.

  .. attribute:: show_traceback
  
    If True, traceback information is included with error responses. Note that
    traceback information is always included in logs. Defaults to True.


  .. method:: application_did_stop()

    Called when the application stops accepting incoming requests.

    The default implementation does nothing.

  .. method:: application_will_start()

    Called just before the application starts accepting incoming requests.

    The default implementation does nothing.

  .. method:: error(typ, val, tb)

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

    If :attr:`show_traceback` evaluates to true, the
    error message will also include a somewhat detailed backtrace. You should
    disable :attr:`show_traceback` in production
    environments.
  
    :param typ: Exception type
    :param val: Exception value
    :param tb:  Traceback

  .. method:: exit()

    Exit application.

  .. method:: run()

    Run application.

  .. method:: service()

    Service a request.



.. --------------------------------------------------------------------------------------------------------



.. class:: Request

  A HTTP request
  

  .. attribute:: input

    Input stream.

    If you send any data which is neither ``x-www-form-urlencoded`` nor ``multipart`` format, you will be able to read the raw POST body from this stream.

    You could read ``x-www-form-urlencoded`` or ``multipart`` POST requests in raw format, but you have to read from this stream before calling any of `post` or `files`, since they will otherwise trigger the built-in parser and read all data from the stream.

    Example, parsing a JSON request::

     from smisk.core import *
     from smisk.serialization.json import json_decode
     class App(Application):
       def service(self):
         if request.env['REQUEST_METHOD'] == 'POST':
           response('Input: ', repr(json_decode(self.request.input.read())), "\n")
 
     App().run()

    You could then send a request using curl for example::

      curl --data-binary '{"Url": "http://www.example.com/image/481989943", "Position": [125, "100"]}' http://localhost:8080/
  
    :type: :class:`~smisk.core.Stream`


  .. attribute:: error
  
    :type: :class:`~smisk.core.Stream`


  .. attribute:: env
  
    HTTP transaction environment.
  
    :type: dict


  .. attribute:: url
  
    Reconstructed URL
  
    For example; if you need to know if running under SSL::
  
      if request.url.scheme == 'https':
        response('Secure connection')
      else:
        response('Big brother is watching you')
  
    :type: :class:`~smisk.core.URL`


  .. attribute:: get

    Parameters passed in the query string part of the URL
  
    :type: dict


  .. attribute:: post
  
    Parameters passed in the body of a POST request
  
    :type: dict


  .. attribute:: files
  
    Any files uploaded via a POST request
  
    :type: dict


  .. attribute:: cookies
  
    Any cookies that was attached to the request
  
    :type: dict


  .. attribute:: session
  
    Current session.
  
    Any modifications to the session must be done before output has begun, as it
    will add a ``Set-Cookie:`` header to the response.
  
    :type: object


  .. attribute:: session_id
  
    Current session id
  
    :type: str


  .. attribute:: is_active
  
    Indicates if the request is active, if we are in the middle of a 
    *HTTP transaction*
  
    :type: bool


  .. attribute:: referring_url

    .. versionadded:: 1.1.0
  
    :type: :class:`~smisk.core.URL`


  .. attribute:: method

    .. versionadded:: 1.1.1
  
    HTTP method ("GET", "POST", etc.).
  
    :see: `RFC 2616, HTTP 1.1, Method Definitions <http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html>`_
    :type: str


  .. attribute:: max_multipart_size

    .. versionadded:: 1.1.2
    
    Limits the amount of data which Smisk normally automatically parses received in a POST or PUT request. For example uploaded files.
    
    Only applies to payloads with a mime-type matching :samp:`multipart/*` – if the payload is defined as another media type, is form data or does not specify a content type – Smisk will not touch the input thus no limits apply (it's up to the code which eventually read the input to set limits).
    
    Setting the value to :samp:`-1` or lower *disables* the limit. Note that this is different from :attr:`max_formdata_size` (which can no be disabled).
    
    Setting the value to :samp:`0` (zero) disables automatic multipart parsing (any multipart input will be left intact/unread).
    
    .. note:
      
      Smisk uses a on-the-fly streaming multipart parser which writes uploaded files directly to disk. This means that :samp:`max_payload_size` can safely be set to a relatively high value without risking DoS vulnerability.
    
    :type: long
    :default: 2147483648 (2 GB)
    :see: :attr:`max_formdata_size`.
  
  
  .. attribute:: max_formdata_size

    .. versionadded:: 1.1.2
    
    Limits the amount of data which Smisk will accept in a :samp:`*/x-www-form-urlencoded` payload.
    
    Setting the value to :samp:`0` (zero) disables automatic form data parsing (any form data input will be left intact/unread).
    
    Note that – in contrast to :attr:`max_multipart_size` – this limit can not be disabled, only adjusted.
    
    :type: long
    :default: 10737418 (10 MB)
    :see: :attr:`max_multipart_size`


  .. method:: log_error(message)

    Log something through :attr:`error` including process name and id.
  
    Normally, :attr:`error` ends up in the host server error log.



.. --------------------------------------------------------------------------------------------------------




.. class:: Response
  
  A HTTP response.
  
  
  
  .. attribute:: headers
    
    Response headers.
    
    :type: list
  
  
  .. attribute:: out
    
    Output stream.
    
    :type: :class:`Stream`
  
  
  .. attribute:: has_begun
  
    Indicates if the response has begun.
    
    Check if output (http headers & possible body) has been sent to the client.
    
    Read-only.
    
    True if :meth:`begin()` has been called and output has started, otherwise :samp:`False`.
    
    :type: bool
  
  
  
  
  .. method:: __call__(*strings)
  
    Respond with a series of byte strings.
    
    This is equivalent of calling :meth:`writelines(strings) <writelines>`, thus
    if :meth:`begin()` has not yet been called, it will be. Calling without
    any arguments has no effect. Note that the arguments must be strings, as
    this method actually uses writelines.
  

  .. method:: send_file(path)
    
    Send a file to the client by using the host server sendfile-header
    technique.
    
    :param  path: If this is a relative path, the host server defines the
                  behaviour.
    :type   path: string
    
    :raises EnvironmentError: If smisk does not know how to perform *sendfile*
                              through the current host server or if response 
                              has already started.
    :raises IOError:
  
  
  .. method:: begin()
  
    Begin response - send headers.
    
    Automatically called by mechanisms like :meth:`write()` and :meth:`Application.run()`.
    
    :raises EnvironmentError: if response has already started.
  
    
  .. method:: write(str)
  
    Write *str* bytes to :attr:`out` output stream.
    
    :meth:`begin()` will be called if response has not yet begun.
    
    :param    string: Data.
    :type     string: str
    :raises   IOError:
  
  
  .. method:: writelines(lines)
  
    Write a sequence of byte strings to the output stream.
    
    The sequence *lines* can be any iterable object producing strings,
    typically a list or tuple of strings. There is no return value. (This
    interface matches that of the Python file object readlines() and
    writelines())
    
    Does not add line separators or modify the strings in any way.
    
    This method esentially calls :meth:`begin()` if not :attr:`has_begun`, then
    calls :samp:`out.writelines(lines)`. The difference between calling 
    :meth:`writelines()` (this method) and :samp:`out.writelines()` 
    (:meth:`Stream.writelines()`) is that the latter will not call 
    :meth:`begin()` if needed. You should always use this method instead of 
    :samp:`out.writelines()`, unless you are certain :meth:`begin()` has been
    called. (:samp:`begin()` is automatically called upon after a
    :samp:`service()` call if it has not been called, so you can not count on 
    it not being called at all.)
    
    :param  lines: A sequence of byte strings
    :type   lines: iterable
    :raises IOError:
    
    
  .. method:: find_header(name) -> int
  
    Find a header in the list of :attr:'headers' matching *prefix* in a
    case-insensitive manner.
    
    :param  name: Name or prefix of a header. i.e. "Content-type:" or "Content".
    :type   name: str
    :returns: Index in :attr:'headers' or :samp:`-1` if not found.
  
  
  .. method:: set_cookie(name, value[, comment, domain, path, secure, version, max_age, http_only])
  
    Set a cookie.
    
    Setting a cookie effectively appends a header to :attr:`headers`. The
    cookie set will **not** be made available in :attr:`Request.cookies`.
    
    :type  name:    string
    :param name:    The name of the state information (*cookie*). names that begin with $ are reserved for other uses and must not be used by applications.

    :type  value:   string
    :param value:   Opaque to the user agent and may be anything the origin server chooses to send, possibly in a server-selected printable ASCII encoding. *Opaque* implies that the content is of interest and relevance only to the origin server. The content may, in fact, be readable by anyone that examines the Set-Cookie header.

    :type  comment: string
    :param comment: Optional. Because cookies can contain private information about a user, the Cookie attribute allows an origin server to document its intended use of a cookie. The user can inspect the information to decide whether to initiate or continue a session with this cookie.

    :type  domain:  string
    :param domain:  Optional. The Domain attribute specifies the domain for which the cookie is valid. An explicitly specified domain must always start with a dot.

    :type  path:    string
    :param path:    Optional. The Path attribute specifies the subset of URLs to which this cookie applies.

    :type  secure:  bool
    :param secure:  Optional. The Secure attribute directs the user agent to use only (unspecified) secure means to contact the origin server whenever it sends back this cookie. The user agent (possibly under the user's control) may determine what level of security it considers appropriate for *secure* cookies. The Secure attribute should be considered security advice from the server to the user agent, indicating that it is in the session's interest to protect the cookie contents.

    :type  version: int
    :param version: Optional. The Version attribute, a decimal integer, identifies to which version of the state management specification the cookie conforms. For the `RFC 2109 <http://www.faqs.org/rfcs/rfc2109.html>`__ specification, Version=1 applies. If not specified, this will be set to ``1``.

    :type  max_age: int
    :param max_age: The value of the Max-Age attribute is delta-seconds, the lifetime of the cookie in seconds, a decimal non-negative integer. To handle cached cookies correctly, a client **should** calculate the age of the cookie according to the age calculation rules in the `HTTP/1.1 specification <http://www.faqs.org/rfcs/rfc2616.html>`__. When the age is greater than delta-seconds seconds, the client **should** discard the cookie. A value of zero means the cookie **should** be discarded immediately (not when the browsers closes, but really immediately)

    :type  http_only: bool
    :param http_only: When True the cookie will be made accessible only through the HTTP protocol. This means that the cookie won't be accessible by scripting languages, such as JavaScript. This setting can effectly help to reduce identity theft through `XSS attacks <http://en.wikipedia.org/wiki/Cross-site_scripting>`__ (although it is not supported by all browsers).
    
    .. Note::
      Setting a cookie will cause the response not to be cached by proxies or peer browsers.

    .. Seealso::
      `RFC 2109 <http://www.faqs.org/rfcs/rfc2109.html>`__ - *HTTP State Management Mechanism*




.. --------------------------------------------------------------------------------------------------------



.. class:: Stream

  A file-like I/O stream connected to the host server.
  
  TODO



.. --------------------------------------------------------------------------------------------------------



.. class:: SessionStore(object)

  Basic session store type


  .. attribute:: ttl
  
    For how long a session should be valid, expressed in seconds.
  
    Defaults to 900.
  
    :type: int


  .. attribute:: name

    Name used to identify the session id cookie.
  
    Defaults to ``"SID"``.
  
    :type: string



.. --------------------------------------------------------------------------------------------------------


.. class:: FileSessionStore(SessionStore)

  Basic session store which uses files
  
  :see: :class:`~smisk.core.SessionStore`


  .. attribute:: file_prefix
    
      A string to prepend to each file stored in ``dir``.
    
      Defaults to ``tempfile.tempdir + "smisk-sess."`` – for example:
      ``/tmp/smisk-sess.``

      :type: string


  .. attribute:: gc_probability

    .. versionadded:: 1.1.0
  
    A value between 0 and 1 which defines the probability that sessions are
    garbage collected.

    Garbage collection is only triggered when trying to read a session object,
    so this only effects requests which involves reading sessions.

    Defaults to ``0.1`` (10% probability)

    :type: float
  

  .. method:: read(session_id) -> data

    :param  session_id: Session ID
    :type   session_id: string
    :raises:  :class:`~smisk.core.InvalidSessionError` if there is no actual
              session associated with *session_id*.
    :rtype: object


  .. method:: write(session_id, data)

    :param  session_id: Session ID
    :type   session_id: string
    :param  data:       Data to be associated with *session_id*
    :type   data:       object


  .. method:: refresh(session_id)

    TODO


  .. method:: destroy(session_id)

    TODO


  .. method:: path(session_id) -> string
  
    Path to file for *session_id*.



.. --------------------------------------------------------------------------------------------------------


.. class:: URL
  
  `Uniform Resource Locator <http://en.wikipedia.org/wiki/Uniform_Resource_Locator>`__

  .. attribute:: scheme
    
    The URL schema, always in lower case.
    
    :type: string
  
  
  .. attribute:: user
    
    :type: string
  
  
  .. attribute:: password
    
    :type: string
  
  
  .. attribute:: host
    
    :type: string
  
  
  .. attribute:: port
    
    Port number. *0* (zero) if unknown or not set.
    
    :type: int
  
  
  .. attribute:: path
    
    :type: string
  
  
  .. attribute:: query
    
    :type: string
  
  
  .. attribute:: fragment
    
    :type: string
  
  
  
  .. method:: __init__(obj) -> URL
  
    Initialize a new URL from *obj*.
    
    If *obj* is a subclass of :class:`URL`, a shallow copy of *obj* will be returned. 
    If *obj* is something else, it will be converted (if needed) into a str and parsed as it 
    would represent a URL. (i.e. ``"protocol://authority:port/path..."``)
  
  
  .. method:: to_s(scheme=True, user=True, password=True, host=True, port=True, port80=True, path=True, query=True, fragment=True) -> str
  
    String representation.

    By passing *False* (or *0* (zero)) for any of the arguments, you can omit certain parts 
    from being included in the string produced. This can come in handy when for example you 
    want to sanitize away password or maybe not include any path, query or fragment.
    
    If a string is passed for one of the keyword arguments, that string is used instead
    of the value stored inside the URL object::
    
      >>> from smisk.core import URL
      >>> URL('http://host.name:1234/some/path').to_s()
      'http://host.name:1234/some/path'
      >>> URL('http://host.name:1234/some/path').to_s(host='another.host')
      'http://another.host:1234/some/path'
    
    In some cases, you may not want to include certain port numbers (80 and 443 in most cases)::
    
      >>> from smisk.core import URL
      >>> url = URL('https://host:443/some/path')
      >>> url.to_s(port=url.port not in (80,443))
      'https://host/some/path'
    
    :rtype: str
    :aliases: to_str, __str__
  
  
  .. staticmethod:: encode(s) -> basestring
    
    Encode any unsafe or reserved characters in a given string for use in URI and URL contexts.

    The difference between encode and escape is that this function encodes characters 
    like / and : which are considered safe for rendering url's, but not for using as a 
    component in path, query or the fragment.

    In other words: Use :meth:`encode()` for path, query and fragment components.
    Use :meth:`escape()` on whole URLs for safe rendering in other contexts.

    Characters being escaped: ``$ &+,/;=?<>"#%{}|\^~[]`@``:
    Also low and high characters ``(< 33 || > 126)`` are encoded.

    :param  s:
    :type   s: basestring
    :raises TypeError: if *s* is not a str or unicode
  
  
  
  .. staticmethod:: escape(s) -> basestring
    
    Escape unsafe characters ``<> "#%{}|\^~[]`@:\033`` in a given string for use in URI and URL contexts.
    
    See documentation of :meth:`encode()` to find out about the differences.
    
    :param  s:
    :type   s: basestring
    :raises TypeError: if *s* is not a str or unicode
  
  
  
  .. staticmethod:: decode(s) -> basestring
    
    Restore data previously encoded by :meth:`encode()` or :meth:`escape()`.

    Done by transforming the sequences ``%HH`` to the character represented by 
    the hexadecimal digits ``HH``.

    :param  str:
    :type   str: basestring
    :raises TypeError: if *s* is not a str or unicode
    :aliases: unescape
  
  
  .. staticmethod:: decompose_query(string, charset='utf-8') -> str
  
    Parses a query string into a dictionary.
    
    .. code-block:: python
      
      >>> from smisk.core import URL
      >>> print URL.decompose_query('name=Jack%20%C3%B6l&age=53')
      {'age': '53', 'name': 'Jack \xc3\xb6l'}
      
    
    :param  charset:
      Character encoding of *s* used to create unicode values and normalized str keys.
      If *charset* is ``None``, a `str` (bytes) is returned instead of a `unicode`.
    :type   charset: str





Exceptions
-------------------------------------------------

.. exception:: Error

.. exception:: IOError

.. exception:: InvalidSessionError


Modules
-------------------------------------------------

.. toctree::
  :maxdepth: 1
  
  smisk.core.bsddb
  smisk.core.xml
