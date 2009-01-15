:mod:`smisk.ipc.bsddb` --- Berkeley DB IPC backend
===========================================================

.. module:: smisk.ipc.bsddb
.. versionadded:: 1.1.2


Module contents
-------------------------------------------------

.. function:: shared_dict(homedir=None, name=None, mode=0600, dbenv=None, type=db.DB_HASH, flags=db.DB_CREATE) -> DBDict

  Convenience function to create and/or return a DBDict.


.. class:: DBDict(MutableMapping)
  
  TODO


.. class:: DBDictError(db.DBError)
  
  TODO

.. class:: DBDictCursor
  
  TODO
