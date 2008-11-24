:class:`smisk.core.Request` --- A HTTP request
===========================================================

.. class:: smisk.core.Request

  A HTTP request


Instance attributes
-------------------------------------------------

.. attribute:: smisk.core.Request.input

  Input stream.

  If you send any data which is neither ``x-www-form-urlencoded`` nor ``multipart`` format, you will be able to read the raw POST body from this stream.

  You could read ``x-www-form-urlencoded`` or ``multipart`` POST requests in raw format, but you have to read from this stream before calling any of `post` or `files`, since they will otherwise trigger the built-in parser and read all data from the stream.

  **Example of how to parse a JSON request:**::

   import cjson as json
   from smisk.core import *
   class App(Application):
     def service(self):
       if request.env['REQUEST_METHOD'] == 'POST':
         response('Input: ', repr(json.decode(self.request.input.read())), "\n")
 
   App().run()

  You could then send a request using curl for example::

    curl --data-binary '{"Url": "http://www.example.com/image/481989943", "Position": [125, "100"]}' http://localhost:8080/
  
  :type: :class:`smisk.core.Stream`


.. attribute:: smisk.core.Request.error
  
  :type: :class:`smisk.core.Stream`


.. attribute:: smisk.core.Request.env
  
  HTTP transaction environment.
  
  :type: dict


.. attribute:: smisk.core.Request.url
  
  Reconstructed URL
  
  :type: :class:`smisk.core.URL`


.. attribute:: smisk.core.Request.get

  Parameters passed in the query string part of the URL
  
  :type: dict


.. attribute:: smisk.core.Request.post
  
  Parameters passed in the body of a POST request
  
  :type: dict


.. attribute:: smisk.core.Request.files
  
  Any files uploaded via a POST request
  
  :type: dict


.. attribute:: smisk.core.Request.cookies
  
  Any cookies that was attached to the request
  
  :type: dict


.. attribute:: smisk.core.Request.session
  
  Current session.
  
  Any modifications to the session must be done before output has begun, as it
  will add a ``Set-Cookie:`` header to the response.
  
  :type: object


.. attribute:: smisk.core.Request.session_id
  
  Current session id
  
  :type: string


.. attribute:: smisk.core.Request.is_active
  
  Indicates if the request is active, if we are in the middle of a 
  *HTTP transaction*
  
  :type: bool


.. attribute:: smisk.core.Request.referring_url

  .. versionadded:: 1.1
  
  :type: :class:`smisk.core.URL`


Instance methods
-------------------------------------------------

.. method:: smisk.core.Request.log_error(self, message)

  Log something through ``errors`` including process name and id.
  
  Normally, ``errors`` ends up in the host server error log.

