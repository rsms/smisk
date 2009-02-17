# encoding: utf-8
'''XML infoset generic serializer.

See: http://msdn.microsoft.com/en-us/library/bb924435.aspx
'''
from smisk.serialization.xmlbase import *
from datetime import datetime
from smisk.util.DateTime import DateTime
from smisk.util.type import *

__all__ = ['XMLInfosetSerializer']

class XMLInfosetSerializer(XMLSerializer):
  '''Generic XML infoset
  '''
  name = 'XML infoset'
  extensions = ('xml',)
  media_types = ('text/xml',)
  charset = 'utf-8'
  
  xml_root_name = 'root'
  
  @classmethod
  def build_object(cls, parent, name, value):
    e = Element(name)
    if isinstance(value, datetime):
      e.set('type', u'date')
      e.text = DateTime(value).as_utc().strftime('%Y-%m-%dT%H:%M:%SZ')
    elif isinstance(value, StringTypes):
      e.set('type', u'string')
      e.text = value
    elif isinstance(value, data):
      e.set('type', u'data')
      e.text = value.encode()
    elif isinstance(value, (int, float, long)):
      e.set('type', u'number')
      e.text = unicode(value)
    elif value is None:
      e.set('type', u'null')
    elif isinstance(value, DictType):
      e.set('type', u'object')
      for k in value:
        cls.build_object(e, k, value[k])
    elif isinstance(value, (list, tuple)):
      e.set('type', u'array')
      for v in value:
        if isinstance(v, (int, float, long)):
          v = unicode(v)
        cls.build_object(e, u'item', v)
    else:
      e.set('type', u'string')
      e.text = unicode(value)
    parent.append(e)
  
  @classmethod
  def build_document(cls, d):
    root = Element(cls.xml_root_name, type=u'object')
    for k in d:
      cls.build_object(root, k, d[k])
    return root
  

# Only register if xml.etree is available
if ElementTree is not None:
  serializers.register(XMLInfosetSerializer)

if __name__ == '__main__':
  if 0:
    try:
      raise Exception('Mosmaster!')
    except:
      from smisk.mvc.http import InternalServerError
      print XMLInfosetSerializer.serialize_error(InternalServerError, {
        'code': 123,
        'description': u'something really bad just went down'
      }, 'utf-8')
      import sys
      sys.exit(0)
  charset, xmlstr = XMLInfosetSerializer.serialize({
    'title': 'Spellistan frum hell',
    'creator': 'rasmus',
    'date': DateTime.now(),
    'tracks': (
      {
        'location': 'spotify:track:0yR57jH25o1jXGP4T6vNGR',
        'identifier': 'spotify:track:0yR57jH25o1jXGP4T6vNGR',
        'title': 'Go Crazy (feat. Majida)',
        'creator': 'Armand Van Helden',
        'album': 'Ghettoblaster',
        'trackNum': 1,
        'duration': 410000
      },
      {
        'location': 'spotify:track:0yR57jH25o1jXGP4T6vNGR',
        'identifier': 'spotify:track:0yR57jH25o1jXGP4T6vNGR',
        'title': None,
        'creator': 'Armand Van Helden2',
        'internets': [
          123,
          456.78,
          u'moset'
        ],
        'album': 'Ghettoblaster2',
        'trackNum': 2,
        'duration': 410002
      },
      {
        'location': 'spotify:track:0yR57jH25o1jXGP4T6vNGR',
        'identifier': 'spotify:track:0yR57jH25o1jXGP4T6vNGR',
        'title': 'Go Crazy3 (feat. Majida)',
        'creator': data('Armand Van Helden3'),
        'album': 'Ghettoblaster3',
        'trackNum': 3,
        'duration': 410007
      },
    )
  }, 'utf-8')
  print xmlstr
  #from StringIO import StringIO
  #print repr(XMLInfosetSerializer.unserialize(StringIO(xmlstr)))
