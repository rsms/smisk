:mod:`smisk.autoreload`
===========================================================

.. module:: smisk.autoreload
.. versionadded:: 1.1

Automatically reload processes when components are updated.

Reloads modules and configuration files.


Configuration parameters
-------------------------------------------------

.. describe:: smisk.autoreload

  Enable automatic reloading of modules and configuration files upon modification.
  
  Acts as the default value for the *smisk.autoreload.modules* and *smisk.autoreload.config* parameters.
  
  In this case, where only *smisk.autoreload* is set and defined as True, both
  modules and configuration files will be monitored for changes:
  
  .. code-block:: javascript
  
    "smisk.autoreload": true
  
  In this case, both modules and configuration files will be monitored for
  changes, because *smisk.autoreload.modules* will inherith the value ``true``:
  
  .. code-block:: javascript
  
    "smisk.autoreload": true,
    "smisk.autoreload.config": true
  
  In this case, only configuration files will be monitored
  since *smisk.autoreload.modules* will inherit the value ``false`` from
  *smisk.autoreload* (it's not explicitly defined and therefore falls back to
  its default value, *which smisk.autoreload.modules* inherit):
  
  .. code-block:: javascript
  
    "smisk.autoreload.config": true
  
  :default: :samp:`False`
  :type: bool


.. describe:: smisk.autoreload.modules

  Enable automatic reloading of modules upon modification.
  
  If True when calling :meth:`smisk.util.main.Main.run()`, a 
  new :class:`Autoreloader` is created and activated.
  
  :default: :samp:`False`
  :type: bool


.. describe:: smisk.autoreload.config

  Enable automatic reloading of configuration files upon modification.
  
  If True when calling :meth:`smisk.util.main.Main.run()`, a 
  new :class:`Autoreloader` is created and activated.
  
  :default: :samp:`False`
  :type: bool


Module contents
-------------------------------------------------

.. class:: smisk.autoreload.Autoreloader(smisk.util.threads.Monitor)

  * Terminates the process when modules change.
  
  * Calls :meth:`smisk.config.Configuration.reload()` on :attr:`smisk.config.config` 
    when a configuration file is modified.
  
  In the context of FastCGI applications, this *should* mean that the
  application is reloaded. Future versions might change this behaviour and add
  "real" reloading of modules.
  
  Subclass of :class:`smisk.util.threads.Monitor`
  
  .. method:: __init__(frequency=1, match=None)
  
  .. method:: run()

    Reload the process if registered files have been modified.

  .. method:: setup()

  .. method:: start()

    Start our own perpetual timer thread for self.run.

