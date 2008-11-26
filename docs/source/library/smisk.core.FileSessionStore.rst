:class:`smisk.core.FileSessionStore` --- File-based session store
=================================================================

.. class:: smisk.core.FileSessionStore(smisk.core.SessionStore)

  Basic session store which uses files
  
  :see: :class:`~smisk.core.SessionStore`


Instance attributes
-------------------------------------------------

.. attribute:: smisk.core.FileSessionStore.file_prefix
    
    A string to prepend to each file stored in ``dir``.
    
    Defaults to ``tempfile.tempdir + "smisk-sess."`` – for example:
    ``/tmp/smisk-sess.``

    :type: string


.. attribute:: smisk.core.FileSessionStore.gc_probability

  .. versionadded:: 1.1
  
  A value between 0 and 1 which defines the probability that sessions are
  garbage collected.

  Garbage collection is only triggered when trying to read a session object,
  so this only effects requests which involves reading sessions.

  Defaults to ``0.1`` (10% probability)

  :type: float
  

Instance methods
-------------------------------------------------

.. method:: smisk.core.FileSessionStore.read(session_id) -> data

  :param  session_id: Session ID
  :type   session_id: string
  :raises:  :class:`~smisk.core.InvalidSessionError` if there is no actual
            session associated with *session_id*.
  :rtype: object


.. method:: smisk.core.FileSessionStore.write(session_id, data)

  :param  session_id: Session ID
  :type   session_id: string
  :param  data:       Data to be associated with *session_id*
  :type   data:       object


.. method:: smisk.core.FileSessionStore.refresh(session_id)

  TODO


.. method:: smisk.core.FileSessionStore.destroy(session_id)

  TODO


.. method:: smisk.core.FileSessionStore.path(session_id) -> string
  
  Path to file for *session_id*.

