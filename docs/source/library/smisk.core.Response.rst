:class:`smisk.core.Response` --- A HTTP response
=================================================

.. module:: smisk.core

.. class:: smisk.core.Response
  
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
      Setting a cookie will cause the response not to be cached by proxies and peer
      browsers.

    .. Seealso::
      `RFC 2109 <http://www.faqs.org/rfcs/rfc2109.html>`__ - *HTTP State Management Mechanism*

