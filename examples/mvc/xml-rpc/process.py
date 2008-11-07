#!/usr/bin/env python
# encoding: utf-8
'''This is a simple but realistic example of a pure XML-RPC service, allowing
only XML-RPC communication. It manages a value, an arbitrary object, which can
be set and aquired.

In order to fit more into this example, we have also overridden the media type
of the XML-RPC serializer, simulating a client that sends requests and accepts
responses only in text/xml.

See config.py for more details.

Using curl, we can trying it out::
  
  # Aquire (or read) the value:
  curl -i -H 'Content-Type: text/xml' -d '<?xml version="1.0"?>
  <methodCall>
    <methodName>examples.getValue</methodName>
  </methodCall>' localhost:8080
  
  # Set (or write) the value:
  curl -i -H 'Content-Type: text/xml' -d '<?xml version="1.0"?>
  <methodCall>
    <methodName>examples.setValue</methodName>
    <params>
      <param>
          <value><string>Goodbye America</string></value>
      </param>
    </params>
  </methodCall>' localhost:8080

'''
from smisk.mvc import *

class root(Controller): pass
class examples(root):
  value = 'Hello World'
  
  def getValue(self):
    return {'value': self.value}
  
  def setValue(self, value):
    self.value = value
  

if __name__ == '__main__':
  main()
