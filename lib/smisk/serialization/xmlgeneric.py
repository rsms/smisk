# encoding: utf-8
'''Generic XML serializer.

Inspired by http://msdn.microsoft.com/en-us/library/bb924435.aspx
'''
from smisk.serialization.xmlbase import *
from datetime import datetime
from smisk.util.DateTime import DateTime
from smisk.util.type import *
from smisk.inflection import inflection
try:
  from elixir import Entity
except ImportError:
  class Undef(object):
    pass
  Entity = Undef()

__all__ = ['GenericXMLSerializer', 'GenericXMLUnserializationError']

T_DATE    = 'date'
T_DATA    = 'data'
T_FLOAT   = 'real'
T_INT     = 'int'
T_DICT    = 'dict'
T_ARRAY   = 'array'
T_STRING  = 'string'
T_NULL    = 'null'
T_TRUE    = 'true'
T_FALSE   = 'false'

class GenericXMLUnserializationError(XMLUnserializationError):
  pass

class GenericXMLSerializer(XMLSerializer):
  '''Generic XML format
  '''
  name = 'Generic XML'
  extensions = ('xml',)
  media_types = ('text/xml',)
  charset = 'utf-8'
  can_serialize = True
  can_unserialize = True
  
  @classmethod
  def build_object(cls, parent, name, value, set_key=True):
    e = ET.Element(name)
    if isinstance(value, datetime):
      e = ET.Element(T_DATE)
      e.text = DateTime(value).as_utc().strftime('%Y-%m-%dT%H:%M:%SZ')
    elif isinstance(value, data):
      e = ET.Element(T_DATA)
      e.text = value.encode()
    elif isinstance(value, float):
      e = ET.Element(T_FLOAT)
      e.text = unicode(value)
    elif isinstance(value, bool):
      if value:
        e = ET.Element(T_TRUE)
      else:
        e = ET.Element(T_FALSE)
    elif isinstance(value, (int, long)):
      e = ET.Element(T_INT)
      e.text = unicode(value)
    elif value is None:
      e = ET.Element(T_NULL)
    elif isinstance(value, DictType):
      e = ET.Element(T_DICT)
      for k in value:
        cls.build_object(e, k, value[k])
    elif isinstance(value, Entity):
      e = ET.Element(T_DICT)
      value = value.to_dict()
      for k in value:
        cls.build_object(e, k, value[k])
    elif isinstance(value, (list, tuple)):
      e = ET.Element(T_ARRAY)
      item_tag = inflection.singularize(name)
      for v in value:
        cls.build_object(e, item_tag, v, False)
    else:
      e = ET.Element(T_STRING)
      e.text = unicode(value)
    if set_key:
      e.set('k', name)
    parent.append(e)
  
  @classmethod
  def parse_object(cls, elem):
    typ = elem.tag
    if typ == T_DATE:
      return DateTime(DateTime.strptime(elem.text, '%Y-%m-%dT%H:%M:%SZ'))
    elif typ == T_DATA:
      return data.decode(elem.text)
    elif typ == T_FLOAT:
      return float(elem.text)
    elif typ == T_INT:
      return int(elem.text)
    elif typ == T_TRUE:
      return True
    elif typ == T_FALSE:
      return False
    elif typ == T_DICT:
      v = {}
      for cn in elem.getchildren():
        k = cn.get('k')
        if not k:
          raise GenericXMLUnserializationError('malformed document -- '\
            'missing "key" attribute for node %r' % elem)
        v[k] = cls.parse_object(cn)
      return v
    elif typ == T_ARRAY:
      v = []
      for cn in elem.getchildren():
        v.append(cls.parse_object(cn))
      return v
    elif typ == T_STRING:
      return elem.text.decode('utf-8')
    elif typ == T_NULL:
      return None
    else:
      raise GenericXMLUnserializationError('invalid document -- unknown type %r' % typ)
  
  @classmethod
  def build_document(cls, d):
    root = ET.Element(T_DICT)
    for k in d:
      cls.build_object(root, k, d[k])
    return root
  
  @classmethod
  def parse_document(cls, elem):
    return cls.parse_object(elem)
  

# Only register if xml.etree is available
if ET is not None:
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
  charset, xmlstr = GenericXMLSerializer.serialize(dict(
      string = "Doodah",
      items = ["A", "B", 12, 32.1, [1, 2, 3, None]],
      float = 0.1,
      integer = 728,
      dict = dict(
        str = "<hello & hi there!>",
        unicode = u'M\xe4ssig, Ma\xdf',
        true_value = True,
        false_value = False,
      ),
      data = data("<binary gunk>"),
      more_data = data("<lots of binary gunk>" * 10),
      date = datetime.now(),
    ), 'utf-8')
  print xmlstr
  from StringIO import StringIO
  print repr(GenericXMLSerializer.unserialize(StringIO(xmlstr)))
