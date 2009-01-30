test
=================================================

.. module:: smisk.test

This module and it's various submodules contain unit tests covering the Smisk
framework. These modules are intentionally undocumented because of it's low
relevance (in the context of API documentation). The source code should be 
sufficient for understanding the tests.

To perform a complete test, simply run the :mod:`smisk.test` module directly:

.. code-block:: sh

  $ python -m smisk.test

You can run a single test suite in a similar manner. To run 
the :class:`~smisk.core.URL` tests for example, we execute this command in a
terminal:

.. code-block:: sh

  $ python -m smisk.test.core.url

