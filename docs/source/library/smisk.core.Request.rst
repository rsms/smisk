:class:`~smisk.core.Request` --- A HTTP request
===========================================================

.. module:: smisk.core
.. class:: smisk.core.Request

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

    .. versionadded:: 1.1
  
    :type: :class:`~smisk.core.URL`


  .. attribute:: method

    .. versionadded:: 1.1.1
  
    HTTP method ("GET", "POST", etc.).
  
    :see: `RFC 2616, HTTP 1.1, Method Definitions <http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html>`_
    :type: str


  .. attribute:: max_multipart_size

    .. versionadded:: 1.1.2
    
    Limits the amount of data which Smisk normally automatically parses received in a POST or PUT request. For example uploaded files.
    
    Only applies to payloads with a mime-type matching :samp:`multipart/*' – if the payload is defined as another media type, is form data or does not specify a content type – Smisk will not touch the input thus no limits apply (it's up to the code which eventually read the input to set limits).
    
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

