# encoding: utf-8
'''
XML-RPC serialization
'''
from . import serializers, BaseSerializer
from xmlrpclib import dumps, loads, Fault

class Serializer(BaseSerializer):
  '''XML-RPC serializer'''
  
  extension = 'xmlrpc'
  media_type = 'application/rpc+xml'
  encoding = 'utf-8'
  
  @classmethod
  def encode(cls, **params):
    return dumps((params,), methodresponse=True, encoding=cls.encoding, allow_none=True)
  
  @classmethod
  def encode_error(cls, params, typ, val, tb):
    return dumps(Fault(getattr(val, 'http_code', 0), str(val)), encoding=cls.encoding)
  
  @classmethod
  def decode(cls, file, length=-1):
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
  

serializers.register(Serializer, ['application/xml-rpc+xml'])
