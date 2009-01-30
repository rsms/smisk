yaml_serial
=================================================

.. versionadded:: 1.1.1
.. module:: smisk.serialization.yaml_serial

YAML: Human-readable data serialization

:Requires: `PyYAML <http://pyyaml.org/wiki/PyYAML>`_


.. class:: YAMLSerializer(Serializer)
  
  .. method:: serialize(params, charset) -> tuple
    
    Write a Python structure into a YAML document.
    
    :Returns: :samp:`(str charset, object doc)`
  
  
  .. method:: serialize_error(status, params, charset=None)
  
  
     
  .. method:: unserialize(file, length=-1, charset=None) -> tuple
    
    Read a YAML document into a Python structure.
    
    :Returns: :samp:`(collection args, dict params)`


.. Seealso::

  `YAML 1.1 <http://yaml.org/spec/1.1/>`_
    YAML 1.1 specification
