:mod:`smisk.core` – Core functionality
===========================================================

This module is the foundation of Smisk and is implemented in machine native code.

See :ref:`c-api` for documentation of the C interface.

.. module:: smisk.core
  :platform: Linux, Mac, Unix
  :synopsis: Smisk core library handling I/O, request and response parsing as 
             well as session handling.

:Requires: `libfcgi <http://www.fastcgi.com/>`_


.. moduleauthor:: Rasmus Andersson <rasmus@flajm.com>


Attributes
-------------------------------------------------

.. attribute:: __build__
  
  Build identifier in URN form, distinguishing each unique build.
  
  *Format changed in version 1.1:* in version 1.0 this 
  was an abritrary (per-build unique) string. In 1.1 this is now a 
  uniform URN.


.. attribute:: app
  
  Current `Application` (``None`` if no application has been created) 
  See also: :attr:`Application.current`.

  .. versionadded:: 1.1


.. attribute:: request
  
  Current `Request` (``None`` if no application is running).

  .. versionadded:: 1.1


.. attribute:: response
  
  Current `Response` (``None`` if no application is running).

  .. versionadded:: 1.1


Functions
-------------------------------------------------

.. function:: bind(path[, backlog=-1])
  
  Bind to a specific unix socket or host (and/or port).
  
  :param path: The Unix domain socket (named pipe for WinNT), hostname, 
               hostname and port or just a colon followed by a port number. 
               e.g. ``"/tmp/fastcgi/mysocket"``, ``"some.host:5000"``, 
               ``":5000"``, ``"\*:5000"``.
  :type  path: string
  :param backlog: The listen queue depth used in the :func:'listen()' call. Set 
                  to negative or zero to let the system decide (recommended).
  :type  backlog: int
  :raises: `smisk.IOError` If already bound.
  :raises: `IOError` If socket creation fails.
  :see: :func:`unbind()`, :func:`listening()`


.. function:: unbind()
  
  Unbind from a previous call to :func:`bind()`.
  
  If not bound, calling this function has no effect. You can test wherethere or
  not the current process is bound by calling :func:`listening()`.

  .. versionadded:: 1.1
  
  :raises: IOError on failure.


.. function:: listening() -> string
  
  Find out if this process is a "remote" process, bound to a socket by means of 
  calling :func:`bind()`. If it is listening, this function returns the address and 
  port or the UNIX socket path.
  
  See also: :func:`unbind()`
  
  :raises: smisk.IOError On failure.
  :returns: Bound path/address or None if not bound.


.. function:: uid(nbits[, node=None]) -> string
  
  Generate a universally Unique Identifier.
  
  See documentation of :func:`pack()` for an overview of :func:``nbits``.
  
  The UID is calculated like this::
    
    sha1 ( time.secs, time.usecs, pid, random[, node] )
  
  ..note::
    
    This is *not* a UUID (ISO/IEC 11578:1996) implementation. However it uses 
    an algorithm very similar to UUID v5 (:rfc:`4122`). Most notably, the format 
    of the output is more compact than that of UUID v5.

  .. versionadded:: 1.1
  
  :param nbits: Number of bits to pack into each byte when creating the string 
                representation. A value in the range 4-6 or 0 in which case 20
                raw bytes are returned. Defaults is 5.
  :type  nbits: int
  :param node:  Optional data to be used when creating the uid.
  :type  node:  string


.. function:: pack(data[, nbits=5]) -> string

  Pack arbitrary bytes into a printable ASCII string.
  
  **Overview of nbits:**
  
  0 bits, No packing:
    20 bytes ``"0x00-0xff"``
  4 bits, Base 16:
    40 bytes ``"0-9a-f"``
  5 bits, Base 32:
    32 bytes ``"0-9a-v"``
  6 bits, Base 64:
    27 bytes ``"0-9a-zA-Z,-"``

  .. versionadded:: 1.1
  
  :param data:
  :type  data:  string
  :param nbits: Number of bits to pack into each byte when creating the string 
                representation. A value in the range 4-6.
  :type  nbits: int
  :see: :func:`uid()`



Exceptions
-------------------------------------------------

.. exception:: Error

.. exception:: IOError

.. exception:: InvalidSessionError


Classes
-------------------------------------------------

.. toctree::
  :glob:
  :maxdepth: 1
  
  **
