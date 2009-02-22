# encoding: utf-8
'''Apple/NeXT Property List serialization.
'''
from smisk.serialization.xmlbase import *
from datetime import datetime
from types import *
import smisk.serialization.plistlib_ as plistlib

__all__ = ['XMLPlistSerializer']

class XMLPlistSerializer(XMLSerializer):
  '''XML Property List serializer
  '''
  name = 'XML Property List'
  extensions = ('plist',)
  media_types = ('application/plist+xml',)
  charset = 'utf-8'
  can_serialize = True
  can_unserialize = True
  
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
  charset, xmlstr = XMLPlistSerializer.serialize(dict(
      string = "Doodah",
      items = ["A", "B", 12, 32.1, [1, 2, 3]],
      float = 0.1,
      integer = 728,
      dict = {
        "str": "<hello & hi there!>",
        "unicode": u'M\xe4ssig, Ma\xdf',
        "true value": True,
        "false value": False,
      },
      data = data("<binary gunk>"),
      more_data = data("<lots of binary gunk>" * 10),
      date = datetime.now(),
    ), None)
  print xmlstr
  from StringIO import StringIO
  print repr(XMLPlistSerializer.unserialize(StringIO(xmlstr)))
