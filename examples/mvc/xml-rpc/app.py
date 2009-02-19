#!/usr/bin/env python
# encoding: utf-8
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
