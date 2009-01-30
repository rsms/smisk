helpers
=================================================

.. module:: smisk.mvc.helpers
.. versionadded:: 1.1.0

All members of this module is exported in :mod:`smisk.mvc`.


.. function:: compose_query(params) -> str

  Convert a mapping object to a URL encoded query string.
  
  The opposite can be found in :meth:`smisk.core.URL.decompose_query()`.
  
  :param params:
  :type  params: dict
  

.. function:: redirect_to(url, entity=None, status=http.Found, **params)

  Redirect the requesting client to someplace else.
  
  *url* can be a string or :class:`~smisk.core.URL` representing a absolute url, relative path or absolute path. Should not include query string information (even though it is possible), but instead use *params* for this purpose.
  
  *entity* should be a :class:`~smisk.mvc.model.Entity` instance or a collection of :class:`~smisk.mvc.model.Entity` instances. The primary keys of these entities are added to *params* along with the actual values.
  
  *params* are composed into a query string and added to the final location.
  
  *status* is the type of HTTP status message to be used. Must be a subclass of :class:`~smisk.mvc.http.Status3xx`.
  
  .. note::
    
    The implementation of this function raises an exception to execute
    the redirection, thus calling this function in your action effectively
    finalizes the current HTTP transaction.
  