# encoding: utf-8
'''
Python pickle serialization
'''
from . import serializers, BaseSerializer
import logging
try:
	from cPickle import dumps, load, loads, HIGHEST_PROTOCOL
except ImportError:
	from pickle import dumps, load, loads, HIGHEST_PROTOCOL

log = logging.getLogger(__name__)


class Serializer(BaseSerializer):
  '''
  Python Pickle Serializer
  
  Example client for interacting with a smisk service:
  >>> import pickle, urllib
  >>> print pickle.load(urllib.urlopen("http://localhost:8080/.pickle?hello=123"))
  '''
  extension = 'pickle'
  media_type = 'application/x-python-pickle'
  encoding = None
  
  @classmethod
  def encode(cls, **params):
    return dumps(params, HIGHEST_PROTOCOL)
  
  @classmethod
  def encode_error(cls, params, typ, val, tb):
    return dumps(dict(code=getattr(val, 'http_code', 0), message=str(val)), HIGHEST_PROTOCOL)
  
  @classmethod
  def decode(cls, file, length=-1):
    # return (list args, dict params)
    if length == 0:
      return (None, None)
    elif length > 0 and length < 1024:
      st = loads(file.read(length))
    else:
      st = load(file)
    if isinstance(st, dict):
      return (None, st)
    elif isinstance(st, list):
      return (st, None)
    else:
      return ((st,), None)
  

serializers.register(Serializer, ['application/x-pickle'])