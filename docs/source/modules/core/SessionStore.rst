:class:`smisk.core.SessionStore` --- Basic session store type
=============================================================

.. class:: smisk.core.SessionStore(object)

  Basic session store type


Instance attributes
-------------------------------------------------

.. attribute:: smisk.core.SessionStore.ttl
  
  For how long a session should be valid, expressed in seconds.
  
  Defaults to 900.
  
  :type: int


.. attribute:: smisk.core.SessionStore.name

  Name used to identify the session id cookie.
  
  Defaults to ``"SID"``.
  
  :type: string
