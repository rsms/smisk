# encoding: utf-8
'''
XML-RPC serialization
'''
from smisk.core import Application
from smisk.mvc import http
from smisk.serialization import serializers, Serializer
from xmlrpclib import dumps, loads, Fault

class XMLRPCSerializer(Serializer):
  '''XML-based Remote Procedure Call
  '''
  
  name = 'XML-RPC'
  extensions = ('xmlrpc',)
  media_types = ('application/rpc+xml', 'application/xml-rpc+xml')
  charset = 'utf-8'
  handles_empty_response = True
  can_serialize = True
  can_unserialize = True
  
  respect_method_name = True
  '''Enable translating <methodName> tag into request path
  '''
  
  @classmethod
  def serialize(cls, params, charset):
    return (charset, dumps((params,), methodresponse=True, encoding=charset, allow_none=True))
  
  @classmethod
  def serialize_error(cls, status, params, charset=None):
    msg = u'%s: %s' % (params['name'], params['description'])
    return (charset, dumps(Fault(params['code'], msg), encoding=charset))
  
  @classmethod
  def unserialize(cls, file, length=-1, encoding=None):
    # return (list args, dict params)
    params, method_name = loads(file.read(length))
    
    # Override request path with mathodName. i.e. method.name -> /method/name
    if cls.respect_method_name:
      if method_name is None:
        raise http.InternalServerError(
          'respect_method_name is enabled but request did not include methodName')
      Application.current.request.url.path = '/'+'/'.join(method_name.split('.'))
    
    args = []
    kwargs = {}
    if len(params) > 0:
      for o in params:
        if isinstance(o, dict):
          kwargs.update(o)
        else:
          args.append(o)
    
    return (args, kwargs)
  

serializers.register(XMLRPCSerializer)
