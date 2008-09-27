# encoding: utf-8
'''
XML-RPC serialization
'''
from smisk.codec import codecs, BaseCodec
from xmlrpclib import dumps, loads, Fault

class codec(BaseCodec):
  '''XML-RPC serializer'''
  
  extensions = ('xmlrpc',)
  media_types = ('application/rpc+xml', 'application/xml-rpc+xml')
  encoding = 'utf-8'
  
  @classmethod
  def encode(cls, **params):
    return dumps((params,), methodresponse=True, encoding=cls.encoding, allow_none=True)
  
  @classmethod
  def encode_error(cls, status, params, typ, val, tb):
    code = params.get('code', status.code)
    msg = params.get('message', status.name)
    return dumps(Fault(code, str(msg)), encoding=cls.encoding)
  
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
  

codecs.register(codec)
