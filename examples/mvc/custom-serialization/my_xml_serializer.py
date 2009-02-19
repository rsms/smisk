# encoding: utf-8
'''Generic XML serialization
'''
from smisk.serialization.xmlbase import *
from datetime import datetime
from smisk.util.DateTime import DateTime
from smisk.util.type import *
try:
  from elixir import Entity
except ImportError:
  class Undef(object):
    pass
  Entity = Undef()

__all__ = ['GenericXMLSerializer']

class GenericXMLSerializer(XMLSerializer):
  '''Generic XML
  
  Maps a Python structure to a similar XML structure, about the same way YQL do
  http://developer.yahoo.com/yql/console/
  '''
  name = 'XML'
  extensions = ('xml',)
  media_types = ('text/xml',)
  charset = 'utf-8'
  
  xml_root_name = 'rsp'
  
  nums_as_attrs = True
  
  @classmethod
  def build_object(cls, parent, name, value, nums_as_attrs=True):
    e = Element(name)
    if isinstance(value, datetime):
      e.text = DateTime(value).as_utc().strftime('%Y-%m-%dT%H:%M:%SZ')
    elif isinstance(value, StringTypes):
      e.text = value
    elif isinstance(value, data):
      e.text = value.encode()
    elif nums_as_attrs and isinstance(value, (int, float, long)):
      parent.set(name, unicode(value))
      return
    elif isinstance(value, DictType):
      for k in value:
        cls.build_object(e, k, value[k], nums_as_attrs)
    elif isinstance(value, Entity):
      value = value.to_dict()
      for k in value:
        cls.build_object(e, k, value[k], nums_as_attrs)
    elif isinstance(value, (list, tuple)):
      #item_name = inflection.singularize(name)
      for v in value:
        if isinstance(v, (int, float, long)):
          v = unicode(v)
        elif isinstance(v, bool):
          v = unicode(v).lower()
        cls.build_object(parent, name, v, nums_as_attrs)
      return
    elif value is not None:
      e.text = unicode(value)
    parent.append(e)
  
  @classmethod
  def build_document(cls, d):
    root = Element(cls.xml_root_name, status=u'ok')
    for k in d:
      cls.build_object(root, k, d[k], cls.nums_as_attrs)
    return root
  
  @classmethod
  def serialize_error(cls, status, params, charset):
    doc = Element(cls.xml_root_name, status=status.name.lower())
    error = Element('error', code=unicode(params['code']), message=unicode(params['description']))
    doc.append(error)
    tb = params.get('traceback')
    if tb:
      traceback = Element('traceback')
      traceback.text = tb
      error.append(traceback)
    return (charset, (cls.xml_declaration % charset) \
      + ElementTree.tostring(doc, charset).encode(charset, cls.unicode_errors))
  

# Only register if xml.etree is available
if ElementTree is not None:
  serializers.register(GenericXMLSerializer)

if __name__ == '__main__':
  if 0:
    try:
      raise Exception('Mosmaster!')
    except:
      from smisk.mvc.http import InternalServerError
      print GenericXMLSerializer.serialize_error(InternalServerError, {
        'code': 123,
        'description': u'something really bad just went down'
      }, 'utf-8')
      import sys
      sys.exit(0)
  charset, xmlstr = GenericXMLSerializer.serialize({
    'title': 'Spellistan frum hell',
    'creator': 'rasmus',
    'date': DateTime.now(),
    'track': (
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
        'title': 'Go Crazy2 (feat. Majida)',
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
  #print repr(GenericXMLSerializer.unserialize(StringIO(xmlstr)))
