:mod:`smisk.mvc.template` --- View in MVC
=================================================

Templating.

:requires: `mako <http://www.makotemplates.org/>`__

.. versionadded:: 1.1.0


Configuration parameters
-------------------------------------------------

.. describe:: smisk.mvc.template.autoreload

  Automatically reload templates which has been modified.

  If this is set to None when the application start accepting requests,
  the application will set the value according to its own autoreload value.
  
  :default: ``False``
  :type: bool


.. describe:: smisk.mvc.template.cache_limit

  Limit cache size.
  0 means no cache. -1 means no limit.
  Any positive value results in a LRU-approach.
  
  :default: :samp:`-1`
  :type: int


.. describe:: smisk.mvc.template.cache_type

  Type of cache. "memory" or "string".
  
  :default: :samp:`"memory"`
  :type: string


.. describe:: smisk.mvc.template.format_exceptions

  Let the templating engine render information about template formatting exceptions.
  
  Things like missing or misspelled variables etc.
  
  :default: :samp:`True`
  :type: bool


.. describe:: smisk.mvc.template.input_encoding

  :default: :samp:`"utf-8"`
  :type: string


.. describe:: smisk.mvc.template.default_filters

  :default: :samp:`["unicode"]`
  :type: list


.. describe:: smisk.mvc.template.errors

  Map http error to a template path.
  Template URI mapped by status codes.
  
  i.e.::
    
    'smisk.mvc.template.errors': {
      500: 'errors/server_error',
      404: 'errors/not_found'
    }
  
  :default: :samp:`{}`
  :type: dict


Classes
-------------------------------------------------

.. autoclass:: smisk.mvc.template.Templates
  :members:
  :undoc-members:


Modules
-------------------------------------------------

.. toctree::

  smisk.mvc.template.filters
