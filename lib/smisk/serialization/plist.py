# encoding: utf-8
'''Apple/NeXT Property List serialization.
'''
from smisk.serialization.xmlbase import *
from datetime import datetime
from types import *
try:
  import plistlib
except ImportError:
  import smisk.serialization.plistlib_ as plistlib

__all__ = ['XMLPlistSerializer', 'plistlib']

class XMLPlistSerializer(XMLSerializer):
  '''XML Property List serializer
  '''
  name = 'XML Property List'
  extensions = ('plist',)
  media_types = ('application/plist+xml',)
  charset = 'utf-8'
  
  @classmethod
  def serialize(cls, params, charset):
    return (cls.charset, plistlib.writePlistToString(params))
  
  @classmethod
  def unserialize(cls, file, length=-1, charset=None):
    # return (list args, dict params)
    st = plistlib.readPlistFromString(file.read(length))
    if isinstance(st, dict):
      return (None, st)
    elif isinstance(st, (list, tuple)):
      return (st, None)
    else:
      return ((st,), None)
  

serializers.register(XMLPlistSerializer)

if __name__ == '__main__':
  charset, xmlstr = XMLPlistSerializer.serialize({
    'message': 'Hello worlds',
    'internets': [
      'interesting',
      'lolz',
      42.0,
      {
        'tubes': [1,3,16,18,24],
        'persons': True,
        'image': data("You bastard! These are pure, innocent bytes you're dealing with.")
      }
    ],
    'today': datetime.now()
  }, None)
  print xmlstr
  from StringIO import StringIO
  print repr(XMLPlistSerializer.unserialize(StringIO(xmlstr)))
