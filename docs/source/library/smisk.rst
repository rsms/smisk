smisk
===========================================================

.. module:: smisk


Modules
-------------------------------------------------

.. toctree::
  :maxdepth: 1
  
  smisk.autoreload
  smisk.charsets
  smisk.config
  smisk.core
  smisk.inflection
  smisk.ipc
  smisk.mvc
  smisk.release
  smisk.serialization
  smisk.session
  smisk.test
  smisk.util
  smisk.wsgi


See :ref:`library <library-index>` for a complete overview of all modules.


Attributes
-------------------------------------------------

.. attribute:: __version__
  
  Library version. I.e. :samp:`1.2.3`
  
  :alias: of :attr:`smisk.release.version`


.. attribute:: __build__
  
  Library build identifier. I.e. :samp:`urn:rcsid:1bb4cbff6045`
  
  :alias: of :attr:`smisk.release.build`


.. attribute:: __author__
  
  Library author(s)
  
  :alias: of :attr:`smisk.release.author`


.. attribute:: __license__
  
  Library license
  
  :alias: of :attr:`smisk.release.license`


.. attribute:: __copyright__
  
  Library copyright information
  
  :alias: of :attr:`smisk.release.copyright`


.. attribute:: app
  
  Current application instance
  
  :see: :attr:`smisk.core.app`


.. attribute:: request
  
  Current request object
  
  :see: :attr:`smisk.core.request`


.. attribute:: response
  
  Current response object
  
  :see: :attr:`smisk.core.response`

