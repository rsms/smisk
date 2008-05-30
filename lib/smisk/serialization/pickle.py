# encoding: utf-8
'''
Python pickle serialization
'''
from . import Serializer as BaseSerializer
from pickle import HIGHEST_PROTOCOL
try:
	from cPickle import dump, dumps, load, loads
except ImportError:
	from pickle import dump, dumps, load, loads


class Serializer(BaseSerializer):
  """Python Pickle Serializer"""
  
  mime_types = ['application/x-pickle', 'application/x-python-pickle']
  '''Pickle MIME types'''
  
  @classmethod
  def encode(cls, st, file):
    return dump(st, file, HIGHEST_PROTOCOL)
  
  @classmethod
  def decode(cls, file):
    return load(file)
  
  @classmethod
  def encodes(cls, st):
    return dumps(st, HIGHEST_PROTOCOL)
  
  @classmethod
  def decodes(cls, string):
    return loads(string)
  
