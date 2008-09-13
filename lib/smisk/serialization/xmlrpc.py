# encoding: utf-8
'''
XMLRPC serialization
'''
from . import serializers, BaseSerializer
from xmlrpclib import dumps, loads, Fault

class Serializer(BaseSerializer):
  '''XMLRPC serializer'''
  
  extension = 'xmlrpc'
  media_type = 'application/rpc+xml'
  encoding = 'utf-8'
  
  @classmethod
  def encode(cls, *args, **params):
    args = list(args)
    args.append(params)
    return dumps(args, None, True, cls.encoding, True)
  
  @classmethod
  def encode_error(cls, typ, val, tb):
    return dumps(Fault(getattr(val, 'http_code', 0), str(val)), encoding=cls.encoding)
  
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
  

serializers.register(Serializer, ['application/xml-rpc+xml'])
