#!/usr/bin/env python
# encoding: utf-8
'''This is a simple, yet realistic, example of a pure XML-RPC service,
allowing only XML-RPC communication. It manages a value, an arbitrary object,
which can be set and aquired.

In order to fit more into this example, we have also overridden the media type
of the XML-RPC serializer, simulating a client that sends requests and accepts
responses only in text/xml.

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

Or using a simple Python client::
  
  # simple test program (from the XML-RPC specification)
  from xmlrpclib import ServerProxy, Error
  service = ServerProxy("http://localhost:8080")
  try:
    print service.examples.getValue()
    print service.examples.setValue("internets rulez")
    print service.examples.getValue()
  except Error, v:
    print "ERROR", v

'''
from smisk.mvc import *

class root(Controller): pass
class examples(root):
  value = 'Hello World'
  
  def getValue(self):
    return {'value': self.value}
  
  def setValue(self, value):
    self.value = value
  

# Aquire the XML-RPC serializer and replace it's media types definition. 
ser = serializers.find('xmlrpc')
ser.media_types = ('text/xml',)

# Unregister all serializers and re-register the XML-RPC serializer,
# effectively only accepting and providing XML-RPC requests and responses.
# If we want to provide other serializers, simply remove or comment out the
# following two lines.
serializers.unregister()
serializers.register(ser)

if __name__ == '__main__':
  config.load('app.conf')
  main()
