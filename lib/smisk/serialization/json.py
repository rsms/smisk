# encoding: utf-8
'''
JSON serialization (RFC 4627)
'''
from . import Serializer as BaseSerializer
try:
	from cjson import encode, decode, DecodeError, EncodeError
except ImportError:
	try:
		from minjson import write as encode, read as decode
		from minjson import ReadException as DecodeError, WriteException as EncodeError
	except ImportError:
		raise ImportError('No JSON implementation available. Install cjson or minjson.')


class Serializer(BaseSerializer):
  """JSON Serializer"""
  
  mime_types = ['application/json']
  '''JSON MIME types'''
  
  @classmethod
  def encode(cls, st, file):
    s = cls.encodes(st)
    file.write(s, len(s))
  
  @classmethod
  def decode(cls, file):
    return decode(file.read())
  
  @classmethod
  def encodes(cls, st):
    return encode(st)
  
  @classmethod
  def decodes(cls, string):
    return decode(string)
  
