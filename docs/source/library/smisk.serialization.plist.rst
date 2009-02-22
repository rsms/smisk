plist
=================================================

.. module:: smisk.serialization.plist
.. versionadded:: 1.1.0

Apple/NeXT Property List serialization.

:DTD: http://www.apple.com/DTDs/PropertyList-1.0.dtd


Example
---------------------------------------

.. code-block:: javascript

  {
    "string": "Doodah",
    "integer": 728,
    "float": 0.1,
    "date": datetime.now(),
    "items": ["A", "B", 12, 32.1, [1, 2, 3]],
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
  
  <?xml version="1.0" encoding="UTF-8"?>
  <!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" 
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
  <plist version="1.0">
    <dict>
      <key>string</key>
      <string>Doodah</string>
      <key>integer</key>
      <integer>728</integer>
      <key>float</key>
      <real>0.10000000000000001</real>
      <key>date</key>
      <date>2009-02-22T17:19:43Z</date>
      <key>items</key>
      <array>
        <string>A</string>
        <string>B</string>
        <integer>12</integer>
        <real>32.100000000000001</real>
        <array>
          <integer>1</integer>
          <integer>2</integer>
          <integer>3</integer>
        </array>
      </array>
      <key>dict</key>
      <dict>
        <key>str</key>
        <string>&lt;hello &amp; hi there!&gt;</string>
        <key>unicode</key>
        <string>Mässig, Maß</string>
        <key>true value</key>
        <true/>
        <key>false value</key>
        <false/>
      </dict>
      <key>data</key>
      <data>PGJpbmFyeSBndW5rPg==</data>
      <key>more_data</key>
      <data>
        PGxvdHMgb2YgYmluYXJ5IGd1bms+PGxvdHMgb2YgYmluYXJ5IGd1bms+PGxvdHMgb2Yg
        YmluYXJ5IGd1bms+PGxvdHMgb2YgYmluYXJ5IGd1bms+PGxvdHMgb2YgYmluYXJ5IGd1
        bms+PGxvdHMgb2YgYmluYXJ5IGd1bms+PGxvdHMgb2YgYmluYXJ5IGd1bms+PGxvdHMg
        b2YgYmluYXJ5IGd1bms+PGxvdHMgb2YgYmluYXJ5IGd1bms+PGxvdHMgb2YgYmluYXJ5
        IGd1bms+
      </data>
    </dict>
  </plist>




Classes
---------------------------------------

.. class:: XMLPlistSerializer(XMLSerializer)
  
  XML Property List serializer.
  
  Note that the None type is not supported by Property List 1.0.
  
  .. attribute:: name
  
    :value: "XML Property List"
  
  
  .. attribute:: extensions
  
    :value: ("plist",)
  
  
  .. attribute:: media_types
  
    :value: ("application/plist+xml",)
  
  
  .. attribute:: charset
  
    :value: "utf-8"
  
  
  .. attribute:: can_serialize
  
    :value: True
  
  
  .. attribute:: can_unserialize
  
    :value: True
  
  
  .. method:: serialize(params, charset):
    
    See :meth:`smisk.serialization.Serializer.serialize()` for more information.
  
  
  .. method:: unserialize(file, length=-1, charset=None):
    
    See :meth:`smisk.serialization.Serializer.unserialize()` for more information.
