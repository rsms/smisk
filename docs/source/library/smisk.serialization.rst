serialization
=================================================

.. module:: smisk.serialization
.. versionadded:: 1.1.0

Data serialization


Attributes
---------------------------------------

.. attribute:: serializers
  
  The serializer registry.
  
  :type: :class:`Registry`



Classes
---------------------------------------

.. class:: data(smisk.serialization.plistlib_.Data)
  
  Represent arbitrary bytes.
  
  .. attribute:: data
    
    Actual storage of the bytes.
    
    :type: str
  
  
  .. method:: __init__(source):
    
    *source* can be a ``str`` or a file-like object with a ``read`` method returning ``str``.
  
  
  .. method:: encode() -> str
  
    Instance method to encode data into a printable, base-64 encoded, string.
  
  
  .. method:: decode(string)
    
    Class method for creating a ``data`` object from a base-64 encoded string.




.. class:: Registry(object)
  
  A serializers registry.
  
  Can be accessed like a dictionary::
  
    >>> reg = Registry()
    >>> # (register some serializers here)
    >>> reg[3]
    <class MySerializer ...
    >>> MySerializer in reg
    True
    >>> for serializer in reg:
    ...   print serializer
    <class Serializer1 ...
    <class Serializer2 ...
  
  
  .. attribute:: first_in
  
    First registered serializer.
  
    :type: :class:`Serializer`
    :value: None
  
  
  .. attribute:: media_types
  
    Media type-to-Serializer map.
  
    :type: dict
    :value: {}
  
  
  .. attribute:: extensions
  
    Filename extension-to-Serializer map.
  
    :type: dict
    :value: {}
  
  
  .. attribute:: serializers
  
    List of available serializers.
  
    :type: list
    :value: []
  
  
  .. attribute:: readers
    
    Iterate serializers able to read, or unserialize, data.
    
    .. code-block:: python
    
      for ser in reg.readers:
        print ser
    
    :rtype: generator
  
  
  .. attribute:: writers
    
    Iterate serializers able to write, or serialize, data.
    
    .. code-block:: python
    
      for ser in reg.writers:
        print ser
    
    :rtype: generator
  
  
  
  
  .. method:: register(serializer)
    
    Register a new :class:`Serializer`.
    
    *serializer* should be the class of the serializer to register, not an instance.


  .. method:: unregister(serializer=None)
    
    Unregister a previously registered :class:`Serializer` or all registered
    serializers, if *serializer* is ``None``.


  .. method:: find(media_type_or_extension)
    
    Find a :class:`Serializer` associated with a media type or an extension.
    
    :rtype: :class:`Serializer`
    :returns: ``None`` if not found.
  
  
  .. method:: associate(serializer, media_type=None, extension=None, override_existing=True)
    
    Associate a :class:`Serializer` with formats and/or extensions.




.. class:: Serializer(object)
  
  Abstract baseclass for serializers.
  
  All members described here are class members (serializers are never instantiated).
  
  
  .. attribute:: name
  
    A human readable short and descriptive name of the serializer.
  
    :type: str
    :value: "Untitled serializer"
  
  
  .. attribute:: extensions
  
    Filename extensions this serializer can handle.
  
    Must contain at least one item.
    The first item will be used as the primary extension.
  
    :type: collection
    :value: tuple()
  
  
  .. attribute:: media_types
  
    Media types this serializer can handle.
  
    Must contain at least one item.
    The first item will be used as the primary media type.
  
    :type: collection
    :value: tuple()
  
  
  .. attribute:: charset
  
    Preferred character encoding.
    
    If the value is ``None`` the serializer is considered "binary".
    
    :type: str
    :value: None
  
  
  .. attribute:: unicode_errors
  
    How to handle unicode conversions.
  
    Possible values: ``"strict", "ignore", "replace", "xmlcharrefreplace", "backslashreplace"``
  
    :type: str
    :value: "strict"
  
  
  .. attribute:: handles_empty_response
    
    If enabled, :meth:`serialize()` will be called even when leafs
    does not generate a response body. (i.e. ``params=None`` passed to :meth:`serialize()`)
  
    Some serialization formats does not allow empty responses (RPC-variants for
    instance) in which case this feature come in handy.
  
    :type: bool
    :value: False
  
  
  .. attribute:: can_serialize
  
    Declares where there or not this serializer can write/encode/serialize data.
  
    .. versionadded:: 1.1.3
    
    :type: bool
    :value: False
  
  
  .. attribute:: can_unserialize
    
    Declares where there or not this serializer can read/decode/unserialize data.
    
    .. versionadded:: 1.1.3
    
    :type: bool
    :value: False
  
  
  
  .. method:: serialize(params, charset) -> tuple
    
    Serialize the data structure *params* with the user/outside-prefered character encoding *charset*.
    
    If the serializer is binary; the first item in the tuple returned should be None. If the serializer is textual; the character encoding *actually used* should be the first item of the tuple returned. It is constructed this way to allow serializers only to accept a few character encodings or to be able to enforce a specific one at the same time as some serializers strictly follow the *charset* requested by the user/outside.
    
    :param params:    Parameters
    :type  params:    dict
    :param charset:   Destination charset. Might be discarded, so care about the returned charset.
    :type  charset:   str
    :returns:         Tuple of ``(str charset, str data)`` where *charset* is the name of the
                      actual charset used and might be ``None`` if binary or unknown. 
                      *data* must be a str.
    :rtype:           tuple
    

  .. method:: unserialize(file, length=-1, charset=None) -> tuple
  
    Unserialize bytes representing some kind of data structure.
    
    :param file:      A file-like object implementing at least the read() method
    :type  file:      object
    :param length:    Number of bytes to read from *file* or ``-1`` if unknown.
    :type  length:    int
    :param charset:   Character encoding of input if the serializer is textual. Might be ``None`` if unknown in which case the :attr:`charset` attribute should be considered.
    :type  charset:   str
    :returns:         Tuple of ``(list args, dict params)``. *args* and *params* might be ``None``.
    :rtype:           tuple
  
  
  .. method:: serialize_error(status, params, charset) -> tuple
    
    Encode an error.
    
    Returning ``None`` indicates that someone else should handle the error encoding. (Normally this means that :meth:`smisk.mvc.Application.error()` serializes the error using best guess).
    
    **"params" will always contain:**
    
      * *code* (int) --- Error code (i.e. ``123``).
      * *name* (unicode) --- Name of the error. i.e. "404 Not Found"
      * *description* (unicode) --- Description of the error or the emtpy string.
      * *server* (unicode) --- Short one line description of the server name, port and software.
    
    **"params" might contain:**
    
      * *traceback* (list) --- A list of strings.
    
    :param status:    HTTP status
    :type  status:    smisk.mvc.http.Status
    :param params:    Parameters
    :type  params:    dict
    :param charset:   Destination charset. Might be discarded, so care about the returned charset.
    :type  charset:   str
    :returns:         Tuple of (str charset, str data) where charset is the name of the
                      actual charset used and might be None if binary or unknown.
    :rtype:           tuple
  
  
  .. method:: add_content_type_header(response, charset)
  
    Sets ``"Content-Type"`` header if missing in response. This method is called by :class:`smisk.mvc.Application` when completing a HTTP transaction and should not be overridden in subclasses (as it)


  .. method:: directions() -> list
    
    List of possible directions, or read/write capabilities.
    
    :returns: ``["read", "write"]``, ``["read"]``, ``["write"]`` or ``[]``
    :rtype: list
  
  
  .. method:: did_register(registry)
    
    Called when this serializer has been successfully registered in a :class:`Registry` (the registry instance is passed as the *registry* argument).
    
    Default implementation does nothing. This is meant to be overridden in
    subclasses to allow a kind of *initialization routine*, setting up
    the serializer if needed.
    
    :type  registry: :class:`Registry`
    :param registry: The registry in which this serializer was registered.
    :rtype: None
  
  
  .. method:: did_unregister(registry)
  
    Called when this serializer has been removed from a :class:`Registry`.
    
    Default implementation does nothing. This is meant to be overridden in
    subclasses to allow a kind of *tear-down routine*, finalizing the serializer
    if needed.
    
    :type  registry: :class:`Registry`
    :param registry: The registry in which this serializer was removed.
    :rtype: None





.. exception:: SerializationError(Exception)
  
  Indicates an encoding error (when converting an object to bytes).


.. exception:: UnserializationError(Exception)

  Indicates an decoding error (when converting bytes to an object).



Modules
---------------------------------------

.. toctree::
  :maxdepth: 1
  
  smisk.serialization.all
  smisk.serialization.json
  smisk.serialization.php_serial
  smisk.serialization.plain_text
  smisk.serialization.plist
  smisk.serialization.python_pickle
  smisk.serialization.python_py
  smisk.serialization.xhtml
  smisk.serialization.xmlbase
  smisk.serialization.xmlgeneric
  smisk.serialization.xmlrpc
  smisk.serialization.xspf
  smisk.serialization.yaml_serial
