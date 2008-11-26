:mod:`smisk.mvc.model`
=================================================

.. versionadded:: 1.1

This module inherits all members of *elixir*


:requires: `elixir <http://elixir.ematia.de/>`__


Configuration parameters
-------------------------------------------------

.. describe:: smisk.mvc.model.bind

  Bind the SQLAlchemy/Elixir metadata.

  This parameter has no default value. If defined, it's actively used to setup a *database engine*.
  
  Example:
  
  .. code-block:: javascript
  
    "smisk.mvc.model.bind": "mysql://user@localhost/database"
  
  :type: string


Module attributes
-------------------------------------------------

.. attribute:: sql

  The *sqlalchemy* module,
  
  Here for your convenience::
  
    from smisk.mvc.model import *
    MyEntity.query().order_by(sql.desc(MyEntity.some_field))
  
