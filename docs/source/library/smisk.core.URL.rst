:class:`smisk.core.URL` --- Uniform Resource Locator
===========================================================

`Uniform Resource Locator <http://en.wikipedia.org/wiki/Uniform_Resource_Locator>`__

.. class:: smisk.core.URL

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
    
    If *obj* is a subclass of :class:`URL`, a shallow copy of *obj* will be returned. If *obj* is something else, it will be, converted to if needed and, treated as bytes which are then parsed like they would represent a (complete or partial) URL.
  
  
  .. method:: to_s(scheme=True, user=True, password=True, host=True, port=True, port80=True, path=True, query=True, fragment=True) -> str
  
    String representation.

    By passing *False* (or *0* (zero)) for any of the arguments, you can omit certain parts from being included in the string produced. This can come in handy when for example you want to sanitize away password or maybe not include any path, query or fragment.
    
    In some cases, you will probably not want to include port 80 or 443::
    
      my_url.to_s(port=my_url.port not in (80,443))
    
    :param  scheme:
    :param  user:
    :param  password:
    :param  host:
    :param  port:
    :param  port80:
    :param  path:
    :param  query:
    :param  fragment:
    :type   scheme:    bool
    :type   user:      bool
    :type   password:  bool
    :type   host:      bool
    :type   port:      bool
    :type   port80:    bool
    :type   path:      bool
    :type   query:     bool
    :type   fragment:  bool
    :rtype: string
    :aliases: to_str, __str__
  
  
  .. staticmethod:: encode(s) -> str
  
  
  .. staticmethod:: escape(s) -> str
  
  
  .. staticmethod:: decode(s) -> str
  
  
  .. staticmethod:: unescape(s) -> str
  
  
  .. staticmethod:: decompose_query(s) -> str
  
