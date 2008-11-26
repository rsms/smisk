:mod:`smisk.release`
===========================================================

.. module:: smisk.release


.. attribute:: version
  
  Library version in the format ``major.minor.build``.
  
  Example: :samp:`1.2.3`
  
  :type: string


.. attribute:: build
  
  Library build identifier.
  
  Not to be confused with the third number in :attr:`version`, which is also called build version)
  
  Example: :samp:`urn:rcsid:1bb4cbff6045`
  
  :type: string


.. attribute:: author
  
  Library author(s)
  
  :type: string


.. attribute:: license
  
  Library license
  
  :type: string


.. attribute:: copyright
  
  Library copyright information
  
  :type: string


.. attribute:: version_info
  
  Structured version info.
  
  A tuple consisting of three integers::
  
    (major, minor, build)
  
  Example: :samp:`(1,1,0)`
  
  :type: tuple
