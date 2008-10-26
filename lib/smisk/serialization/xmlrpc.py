# encoding: utf-8
'''
XML-RPC serialization
'''
from smisk.serialization import serializers, Serializer
from xmlrpclib import dumps, loads, Fault

class serializer(Serializer):
  '''XML-RPC serializer'''
  name = 'XML-RPC'
  extensions = ('xmlrpc',)
  media_types = ('application/rpc+xml', 'application/xml-rpc+xml')
  charset = 'utf-8'
  
  @classmethod
  def serialize(cls, params, charset):
    return (charset, dumps((params,), methodresponse=True, encoding=charset, allow_none=True))
  
  @classmethod
  def serialize_error(cls, status, params, charset=None):
    msg = u' '.join([params['name'], params['description']])
    return (charset, dumps(Fault(params['code'], msg), encoding=charset))
  
  @classmethod
  def unserialize(cls, file, length=-1, encoding=None):
    # return (list args, dict params)
    (params, method_name) = loads(file.read(length))
    args = []
    kwargs = {}
    
    if len(params) > 0:
      for o in params:
        if isinstance(o, dict):
          kwargs.update(o)
        else:
          args.append(o)
    
    return (args, kwargs)
  

serializers.register(serializer)
