ipc
===========================================================

.. module:: smisk.ipc
.. versionadded:: 1.1.2

Inter-process communication


Functions
-------------------------------------------------


.. function:: shared_dict(persistent=False) -> dict

  Aquire the shared dictionary which can be concurrently manipulated by multiple processes.
  
  This is a convenience function which aquires a dict type which is shared between all processes running the same __main__ program. By default, this is simply (a imported reference to) the :func:`~smisk.ipc.bsddb.shared_dict()` function, returning a hashed DBDict stored in shared memory.
  
  There are other implementations available, which all provide the same interface, making future backend swap a simple drop-in operation.
  
  .. note::
    
    By default, the shared dict is backed by bsddb and thus will create a temporary database which is then mapped onto shared memory. When any one Smisk process in an application exit, the database will be *removed*, leaving any living processes without the disk backing. In production, it is recommended you explicitly specify the path for the Berkely DB files by passing the filename or homedir argument to :func:`~smisk.ipc.bsddb.shared_dict()`. You should also pass persisten=True to avoid the files getting deleted.
  
  Example of use in Smisk applications::
    
    from smisk.core import Application, main
    from smisk.ipc import shared_dict
    
    class App(Application):
      def application_will_start(self):
        self.sd = shared_dict()
      
      def service(self):
        # Do something useful with self.sd
        try:
          response = self.sd[request.url.path]
        except KeyError:
          # Build response...
          import os
          response = 'Hello! This was built by process #%d' % os.getpid()
          self.sd[request.url.path] = response
        self.response(response)
    
    main(App)
  
  :param persistent:
    If True, the dictionary will persist between application restarts (i.e.
    the contents of the dict is synced and keept on disk).


Modules
-------------------------------------------------

.. toctree::
  :maxdepth: 1
  
  smisk.ipc.bsddb
  smisk.ipc.memcached

