:mod:`smisk.mvc.model` --- M in MVC
=================================================

.. module:: smisk.mvc.model
.. versionadded:: 1.1

Object Relational Mapper (ORM), normally backed by a RDBMS like SQLite, MySQL or PostgreSQL.

Based on `Elixir <http://elixir.ematia.de/>`__, which in turn is based on
`SQLAlchemy <http://www.sqlalchemy.org/>`__ thus requiring 
`Elixir <http://elixir.ematia.de/>`__ to be installed. If Elixir or SQLAlchemy is not
installed or broken, importing *smisk.mvc.model* will not fail, but rather issue a warning 
and export nothing.

This module inherits & exports all members of *elixir* and exports *sqlalchemy* as :attr:`sql`.


Practical use
-------------------------------------------------

Normally, you import smisk.mvc.model in your module where the entities are defined.

Let's look at one of the example applications; "kittens_orm", which examplifies the basics of `CRUD <http://en.wikipedia.org/wiki/Create,_read,_update_and_delete>`__

::

  kittens_orm/
    app.py
    kittens.conf
    lighttpd.conf

Contents of *app.py*::

  #!/usr/bin/env python
  # encoding: utf-8
  from smisk.mvc import *
  from smisk.mvc.model import *

  class Kitten(Entity):
    name = Field(Unicode(255), primary_key=True)
    color = Field(Unicode(30))
    year_born = Field(Integer)

  class root(Controller):
    def __call__(self, *args, **params):
      return {'kittens': [k.to_dict() for k in Kitten.query.all()]}
  
    def create(self, name, **params):
      kitten = Kitten(name=name, **params)
      redirect_to(u'/read?name=%s' % kitten.name)
    
    def delete(self, name):
      kitten = Kitten.get_by(name=name)
      kitten.delete()
      redirect_to('/')
    
    def read(self, name):
      kitten = Kitten.get_by(name=name)
      return kitten.to_dict()
  
  if __name__ == '__main__':
    main(config='kittens')


Contents of *kittens.conf*:

..code-block:: javascript
  
  "smisk.mvc.model": { "url": "sqlite:///tmp/kittens.sqlite" }




http://localhost:8080/create?name=Busta&color=red


Configuration parameters
-------------------------------------------------

.. describe:: smisk.mvc.model
  
  Configure the underlying Elixir module and SQLAlchemy engine.
  
  If defined, it's actively used to setup a *database engine*.
  This parameter is not set by default.
  
  Example:
  
  .. code-block:: javascript
  
    "smisk.mvc.model": {
      "url": "mysql://user@localhost/database",
      "pool_recycle": 14400,
      "elixir.shortnames": false
    }
  
  :type: dict
  :default: :samp:`None`
  
  **Parameters:**
  
  The dictionary defined for ``smisk.mvc.model`` must contain ``"url"`` and can contain several optional parameters.
  
  
  .. _smisk_mvc_model_url:
  
  .. describe:: url
  
    Indicate the appropriate database dialect and connection arguments.
  
    The URL is a string in the form ``dialect://user:password@host/dbname[?key=value..]``, where dialect is a name such as ``mysql``, ``oracle``, ``postgres``, etc.
  
    This parameter must be defined.
  
    :type: string

  
  .. _smisk_mvc_model_encoding:
  
  .. describe:: encoding
  
    The encoding to be used when encoding/decoding Unicode strings.
  
    :type: string
    :default: :samp:`"utf-8"`


  .. _smisk_mvc_model_convert_unicode:
  
  .. describe:: convert_unicode
  
    True if unicode conversion should be applied to all str types.
  
    :type: bool
    :default: :samp:`False`


  .. _smisk_mvc_model_strategy:
  
  .. describe:: strategy
  
    Allows alternate Engine implementations to take effect.
  
    :type: string
    :default: :samp:`"plain"`
    :see: `SQLAlchemy create_engine() <http://www.sqlalchemy.org/docs/05/sqlalchemy_engine.html#docstrings_sqlalchemy.engine_modfunc_create_engine>`__
  

  .. _smisk_mvc_model_pool_size:
  
  .. describe:: pool_size
  
    The size of the pool to be maintained.
  
    This is the largest number of connections that will be kept persistently in the pool. Note that the pool begins with no connections; once this number of connections is requested, that number of connections will remain.
  
    :type: int
    :default: :samp:`1`


  .. _smisk_mvc_model_pool_recycle:
  
  .. describe:: pool_recycle

    This setting causes the pool to recycle connections after the given number of seconds has passed.
  
    It defaults to -1, or no timeout. For example, setting to 3600 means connections will be recycled after one hour.
  
    .. note::
      
      MySQL in particular will disconnect automatically if no activity is detected on a connection for eight hours (although this is configurable with the MySQLDB connection itself and the server configuration as well). In the case of a MySQL backend, the default value is instead 3600.
  
    :type: int
    :default: :samp:`-1` or :samp:`3600` if the dialect is *MySQL*


  .. _smisk_mvc_model_pool_timeout:
  
  .. describe:: pool_timeout
  
    The number of seconds to wait before giving up on returning a connection.
  
    :type: int
    :default: :samp:`30`


  .. _smisk_mvc_model_max_overflow:
  
  .. describe:: max_overflow
  
    The maximum overflow size of the pool.
  
    When the number of checked-out connections reaches the size set in pool_size, additional connections will be returned up to this limit. When those additional connections are returned to the pool, they are disconnected and discarded. It follows then that the total number of simultaneous connections the pool will allow is ``pool_size + max_overflow``, and the total number of "sleeping" connections the pool will allow is :ref:`pool_size <smisk_mvc_model_pool_size>`. *max_overflow* can be set to -1 to indicate no overflow limit; no limit will be placed on the total number of concurrent connections.
  
    :type: int
    :default: :samp:`10`


  .. _smisk_mvc_model_elixir_shortnames:
  
  .. describe:: elixir.shortnames
  
    If False, table names are deduced only from both module name and entity name.
  
    * If :samp:`True`, entity ``project.fruits.Apple`` -> table ``apple``
    * If :samp:`False`, entity ``project.fruits.Apple`` -> table ``project_fruits_apple``
  
    :type: bool
    :default: :samp:`True`

  
  .. seealso::
    
    `<http://elixir.ematia.de/apidocs/elixir.options.html>`__
      All options available for Elixir. (Note that Elixir options must be prefixed with `elixir.` in the configuration file)
    
    `<http://www.sqlalchemy.org/docs/05/dbengine.html#dbengine_options>`__
      All options available for SQLAlchemy.
  


Module attributes
-------------------------------------------------

.. attribute:: sql

  The *sqlalchemy* module,
  
  Exported for reasons of convenience::
  
    from smisk.mvc.model import *
    MyEntity.query().order_by(sql.desc(MyEntity.some_field))
  

.. attribute:: default_engine_opts
  
  Default options for the `SQLAlchemy create_engine() <http://www.sqlalchemy.org/docs/05/sqlalchemy_engine.html#docstrings_sqlalchemy.engine_modfunc_create_engine>`__ call.
  
  :type: dict

