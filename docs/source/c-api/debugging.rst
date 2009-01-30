.. _c-api-debugging:

Debugging
====================================

When debugging, you should build smisk with ``--debug`` or ``--debug-smisk``:

.. code-block:: sh

  ./setup.py build -f --debug

The argument ``--debug-smisk`` implies ``--debug`` and additionally enables all debug logging and tracing in smisk. The ``--debug`` argument is required for generating sequential code with full symbols.


List information about shared libraries
----------------------------------------

.. code-block:: sh

  $ gdb python
  set args -c "import smisk"
  break exit
  run
  cont # jump past the Python import breakpoint
  # wait for "Reading symbols for shared libraries ... done" have been displayed
  maint info sections ALLOBJ COFF_SHARED_LIBRARY
  kill
