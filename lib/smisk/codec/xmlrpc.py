# encoding: utf-8
'''
XML-RPC serialization
'''
from smisk.codec import codecs, BaseCodec
from xmlrpclib import dumps, loads, Fault

class codec(BaseCodec):
  '''XML-RPC codec'''
  
  extensions = ('xmlrpc',)
  media_types = ('application/rpc+xml', 'application/xml-rpc+xml')
  charset = 'utf-8'
  
  @classmethod
  def encode(cls, params, charset):
    return (charset, dumps((params,), methodresponse=True, encoding=charset, allow_none=True))
  
  @classmethod
  def encode_error(cls, status, params, charset=None):
    msg = u' '.join([params['name'], params['description']])
    return (charset, dumps(Fault(params['code'], msg), encoding=charset))
  
  @classmethod
  def decode(cls, file, length=-1, encoding=None):
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
