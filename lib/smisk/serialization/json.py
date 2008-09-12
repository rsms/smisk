# encoding: utf-8
'''
JSON serialization (RFC 4627)
'''
from . import serializers, BaseSerializer
try:
	from cjson import encode, decode, DecodeError, EncodeError
except ImportError:
	try:
		from minjson import write as encode, read as decode
		from minjson import ReadException as DecodeError, WriteException as EncodeError
	except ImportError:
		raise ImportError('No JSON implementation available. Install cjson or minjson.')


class Serializer(BaseSerializer):
  '''JSON Serializer'''
  extension = '.json'
  output_type = 'application/json'
  output_encoding = 'utf-8'
    
  @classmethod
  def encode(cls, *args, **params):
    if len(args) and len(params):
      return encode((args, params))
    elif len(args):
      return encode(args)
    else:
      return encode(params)
  
  @classmethod
  def encode_error(cls, typ, val, tb):
    return encode(dict(code=getattr(val, 'http_code', 0), message=str(val)))
  
  @classmethod
  def decode(cls, file):
    st = decode(file.read())
    if isinstance(st, dict):
      return (None, None, st)
    elif isinstance(st, list):
      return (None, st, None)
    else:
      return (None, (st,), None)
  


serializers[Serializer.output_type] = Serializer
serializers['application/x-json'] = Serializer
