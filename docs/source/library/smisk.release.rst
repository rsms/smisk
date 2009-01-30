release
===========================================================

.. module:: smisk.release


.. attribute:: version
  
  Library version in the format ``major.minor.build``.
  
  Example: :samp:`"1.2.3"`
  
  :type: str


.. attribute:: build
  
  Library build identifier.
  
  A rcsid-`URN <http://en.wikipedia.org/wiki/Uniform_Resource_Name>`_, specifying the globally unique RCS identifier for the source used to build the current core library.
  
  Example: :samp:`urn:rcsid:1bb4cbff6045`
  
  If Smisk is built from detached source (i.e. source without RCS identification) a utcts-`URN <http://en.wikipedia.org/wiki/Uniform_Resource_Name>`_ is used, containing a epoch timestamp (in Universal Time Coordinate) when the source was built.
  
  In the case of special builds, extra information is available after a thrid colon. For instance Debian packages has an extra :samp:`:debian:N` at the end, where :samp:`N` is the Debian package version (i.e. :samp:`urn:rcsid:1bb4cbff6045:debian:3`).
  
  This is actually defined in :attr:`smisk.core.__build__`, but exposed in this module in order to retain consistency.
  
  :type: str


.. attribute:: author
  
  Library author(s)
  
  :type: str


.. attribute:: license
  
  Library license
  
  :type: str


.. attribute:: copyright
  
  Library copyright information
  
  :type: str


.. attribute:: version_info
  
  Structured version info as a tuple.
  
  Example: :samp:`(1,2,3)`
  
  :type: tuple
