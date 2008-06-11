# encoding: utf-8
'''
XMLRPC serialization
'''
from . import serializers, BaseSerializer
from xmlrpclib import dumps, loads, Fault

class Serializer(BaseSerializer):
  '''XMLRPC serializer'''
  
  output_type = 'application/rpc+xml'
  output_encoding = 'utf-8'
  
  @classmethod
  def encode(cls, *args, **params):
    args = list(args)
    args.append(params)
    return dumps(args, None, True, cls.output_encoding, True)
  
  @classmethod
  def encode_error(cls, typ, val, tb):
    return dumps(Fault(getattr(val, 'http_code', 0), str(val)), encoding=cls.output_encoding)
  
  @classmethod
  def decode(cls, file):
    (params, methodname) = loads(file.read())
    args = []
    kwargs = {}
    
    if len(params) > 0:
      for o in params:
        if isinstance(o, dict):
          kwargs.update(o)
        else:
          args.append(o)
    
    return (methodname, args, kwargs)
  

serializers[Serializer.output_type] = Serializer
serializers['application/xml-rpc+xml'] = Serializer
