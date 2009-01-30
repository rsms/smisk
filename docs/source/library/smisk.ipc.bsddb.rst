bsddb
===========================================================

.. module:: smisk.ipc.bsddb
.. versionadded:: 1.1.2

Berkeley DB IPC backend


Functions
-------------------------------------------------

.. function:: shared_dict(filename=None, homedir=None, name=None, mode=0600, dbenv=None, type=db.DB_HASH, flags=db.DB_CREATE, persistent=False) -> DBDict

  Convenience function to create and/or return a DBDict.



Classes
-------------------------------------------------


.. class:: DBDict(MutableMapping)
  
  TODO

.. class:: DBDictError(db.DBError)
  
  TODO

.. class:: DBDictCursor
  
  TODO
