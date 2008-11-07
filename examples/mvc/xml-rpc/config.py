# encoding: utf-8
# Include traceback with error reponses
app.show_traceback = True

# Aquire the XML-RPC serializer and replace it's media types definition. 
ser = serializers.find('xmlrpc')
ser.media_types = ('text/xml',)

# Unregister all serializers and re-register the XML-RPC serializer,
# effectively only accepting and providing XML-RPC requests and responses.
# If we want to provide other serializers, simply remove or comment out the
# following two lines.
serializers.unregister()
serializers.register(ser)

# Configure logging
logging.basicConfig(
  format='%(levelname)-8s %(name)-20s %(message)s',
  level=logging.DEBUG
)
