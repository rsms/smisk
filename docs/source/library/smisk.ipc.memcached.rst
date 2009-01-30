memcached
===========================================================

.. module:: smisk.ipc.memcached
.. versionadded:: 1.1.2

Memcached IPC backend

:Requires: `cmemcached <http://code.google.com/p/python-libmemcached/>`_ | `memcache <http://www.tummy.com/Community/software/python-memcached/>`_


Functions
-------------------------------------------------

.. function:: shared_dict(name=None, nodes=['127.0.0.1:11211'], memcached_debug=0) -> DBDict

  Convenience function to create and/or return a :class:`MemcachedDict`.


Classes
-------------------------------------------------


.. class:: MemcachedDict(MutableMapping)
  
  TODO

