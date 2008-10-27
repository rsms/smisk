# encoding: utf-8
'''
Python pickle serialization
'''
from smisk.serialization import serializers, Serializer
import logging
try:
  from cPickle import dumps, load, loads, HIGHEST_PROTOCOL
except ImportError:
  from pickle import dumps, load, loads, HIGHEST_PROTOCOL

log = logging.getLogger(__name__)


class PythonPickleSerializer(Serializer):
  '''
  Python Pickle serializer
  
  Example client for interacting with a smisk service::
  
    >>> import pickle, urllib
    >>> print pickle.load(urllib.urlopen("http://localhost:8080/.pickle?hello=123"))
  '''
  name = 'Python Pickle'
  extensions = ('pickle',)
  media_types = ('application/x-python-pickle', 'application/x-pickle')
  
  @classmethod
  def serialize(cls, params, charset):
    return (None, dumps(params, HIGHEST_PROTOCOL))
  
  @classmethod
  def unserialize(cls, file, length=-1, charset=None):
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
  

serializers.register(PythonPickleSerializer)
