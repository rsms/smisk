:mod:`smisk.serialization.json`
=================================================

.. versionadded:: 1.1.0
.. module:: smisk.serialization.json

JSON: JavaScript Object Notation

:see: :rfc:`4627`
:requires: `cjson <http://pypi.python.org/pypi/python-cjson>`_ | minjson


.. function:: json_encode(object) -> str

  Encode python *object*
  
  :raises: :exc:`EncodeError`


.. function:: json_decode(data) -> object

  Decode JSON *data*
  
  :raises: :exc:`DecodeError`


.. class:: smisk.serialization.json.JSONSerializer()
  
  JSON with JSONP support.

  JSONP support through passing the special callback query string parameter.

  .. method:: serialize(params, charset)
     
  .. method:: serialize_error(status, params, charset)
     
  .. method:: unserialize(file, length=-1, charset=None)


.. exception:: DecodeError

  JSON decoding error


.. exception:: EncodeError

  JSON encoding error
