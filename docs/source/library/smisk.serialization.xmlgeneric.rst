xmlgeneric
=================================================

.. module:: smisk.serialization.xmlgeneric
.. versionadded:: 1.1.3

A generic, universal XML serializer with read and write capabilities.

The format is inspired by :mod:`~smisk.serialization.plist` and 
http://msdn.microsoft.com/en-us/library/bb924435.aspx


Example
---------------------------------------

.. code-block:: javascript

  {
    "string": "Doodah",
    "integer": 728,
    "float": 0.1,
    "date": datetime.now(),
    "items": ["A", "B", 12, 32.1, [1, 2, 3, None]],
    "dict": {
      "str": "<hello & hi there!>",
      "unicode": u'M\xe4ssig, Ma\xdf',
      "true value": True,
      "false value": False,
    ),
    "data": data("<binary gunk>"),
    "more_data": data("<lots of binary gunk>" * 10)
  }

.. code-block:: xml
  
  <?xml version="1.0" encoding="utf-8"?>
  <dict>
    <string k="string">Doodah</string>
    <int k="integer">728</int>
    <real k="float">0.1</real>
    <date k="date">2009-02-22T15:46:39Z</date>
    <array k="items">
      <string>A</string>
      <string>B</string>
      <int>12</int>
      <real>32.1</real>
      <array>
        <int>1</int>
        <int>2</int>
        <int>3</int>
        <null />
      </array>
    </array>
    <dict k="dict">
      <false k="false value" />
      <true k="true value" />
      <string k="unicode">Mässig, Maß</string>
      <string k="str">&lt;hello &amp; hi there!&gt;</string>
    </dict>
    <data k="data">PGJpbmFyeSBndW5rPg==</data>
    <data k="more_data">
      PGxvdHMgb2YgYmluYXJ5IGd1bms+PGxvdHMgb2YgYmluYXJ5IGd1bms+PGxvdHMgb2YgYmluYXJ5
      IGd1bms+PGxvdHMgb2YgYmluYXJ5IGd1bms+PGxvdHMgb2YgYmluYXJ5IGd1bms+PGxvdHMgb2Yg
      YmluYXJ5IGd1bms+PGxvdHMgb2YgYmluYXJ5IGd1bms+PGxvdHMgb2YgYmluYXJ5IGd1bms+PGxv
      dHMgb2YgYmluYXJ5IGd1bms+PGxvdHMgb2YgYmluYXJ5IGd1bms+
    </data>
  </dict>


Classes
---------------------------------------

.. class:: GenericXMLSerializer(smisk.serialization.xmlbase.XMLSerializer)
  
  Inherits from :class:`~smisk.serialization.xmlbase.XMLSerializer`
  
  See documentation of :class:`smisk.serialization.Serializer` for details on inherithed methods and how to interface with serializers.
  
  .. attribute:: name
  
    :value: "Generic XML"
  
  .. attribute:: extensions
  
    :value: ("xml",)
  
  .. attribute:: media_types
  
    :value: ("text/xml",)
  
  .. attribute:: charset
  
    :value: "utf-8"
  
  .. attribute:: can_serialize
  
    :value: True
  
  .. attribute:: can_unserialize
  
    :value: True
  
  
  .. method:: build_object(parent, name, value, set_key=True)
    
    Serialize an object.
  
  
  .. method:: parse_object(elem)
    
    Unserialize an object.
  
  
  .. method:: serialize(params, charset):
    
    See :meth:`smisk.serialization.Serializer.serialize()` for more information.
  
  
  .. method:: unserialize(file, length=-1, charset=None):
    
    See :meth:`smisk.serialization.Serializer.unserialize()` for more information.



.. exception:: GenericXMLUnserializationError(smisk.serialization.xmlbase.XMLUnserializationError)
  
  Raised when trying to unserialize invalid documents.
