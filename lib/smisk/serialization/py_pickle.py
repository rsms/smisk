# encoding: utf-8
'''
Python pickle serialization
'''
from . import serializers, BaseSerializer
import pickle, logging
try:
	from cPickle import dumps, load
except ImportError:
	from pickle import dumps, load

log = logging.getLogger(__name__)


class Serializer(BaseSerializer):
  '''
  Python Pickle Serializer
  
  WARNING: Do not use this in production as it is experimental and has some
           known issues.
  '''
  
  output_type = 'application/x-python-pickle'
  
  @classmethod
  def encode(cls, *args, **params):
    if len(args) and len(params):
      return dumps((args, params), pickle.HIGHEST_PROTOCOL)
    elif len(args):
      return dumps(args, pickle.HIGHEST_PROTOCOL)
    else:
      return dumps(params, pickle.HIGHEST_PROTOCOL)
  
  @classmethod
  def encode_error(cls, typ, val, tb):
    return dumps(dict(code=getattr(val, 'http_code', 0), message=str(val)), pickle.HIGHEST_PROTOCOL)
  
  @classmethod
  def decode(cls, file):
    st = load(file)
    if isinstance(st, dict):
      return (None, None, st)
    elif isinstance(st, list):
      return (None, st, None)
    else:
      return (None, (st,), None)
  

serializers['application/x-python-pickle'] = Serializer
serializers['application/x-pickle'] = Serializer