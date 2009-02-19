Smisk
+++++

.. contents ::

Summary
=======

Smisk is a simple, high-performance and scalable web service framework
written in C, but controlled by Python.

It is designed to widen the common bottle necks in heavy-duty web services.

More information at the `Smisk website <http://python-smisk.org/>`_


Getting Started
===============

* Install with ``easy_install smisk``, download from
  `PyPI <http://pypi.python.org/pypi/smisk>`_ or 
  `use a Debian package <http://python-smisk.org/downloads>`_
  
* Have a look at a few `examples <http://python-smisk.org/examples>`_


Examples
========

This is a minimal Smisk service::

  from smisk.core import Application
  class MyApp(Application):
    def service(self):
      self.response.headers = ['Content-Type: text/plain']
      self.response("Hello World!")

  MyApp().run()

And here we have a WSGI compatible application::

  from smisk.wsgi import *
  def hello_app(env, start_response):
    start_response("200 OK", [('Content-Type', 'text/plain')])
    return ["Hello, World!"]

  main(hello_app)

More examples `available here... <http://python-smisk.org/examples>`_


Authors & Contributors
======================
* `Rasmus Andersson <http://hunch.se/>`_ rasmus-flajm.com
* `Eric Moritz <http://themoritzfamily.com/>`_ eric-themoritzfamily.com
* Ludvig Strigeus
