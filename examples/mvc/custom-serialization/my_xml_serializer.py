# encoding: utf-8
'''Example of custom XML serialization
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

__all__ = ['MyXMLSerializer']

class MyXMLSerializer(XMLSerializer):
  '''My custom XML format
  
  Maps a Python structure to a similar XML structure, about the same way YQL do
  http://developer.yahoo.com/yql/console/
  '''
  
  # This is the short name of our serializer. It shows up in reflection, etc.
  name = 'My XML'
  
  # A list of filename extensions we take care of.
  extensions = ('xml',)
  
  # A list of media types we take care of.
  media_types = ('text/xml',)
  
  # The preferred character encoding for responses without any particular
  # requirements.
  charset = 'utf-8'
  
  # This tells Smisk our serializer is able to write, or encode or serialize,
  # data.
  can_serialize = True
  
  # This is an extension of XMLSerializer, defining the name of the root
  # element.
  xml_root_name = 'rsp'
  
  @classmethod
  def build_object(cls, parent, name, value):
    e = ET.Element(name)
    if isinstance(value, datetime):
      e.text = DateTime(value).as_utc().strftime('%Y-%m-%dT%H:%M:%SZ')
    elif isinstance(value, StringTypes):
      e.text = value
    elif isinstance(value, data):
      e.text = value.encode()
    elif isinstance(value, (int, float, long)):
      parent.set(name, unicode(value))
      return
    elif isinstance(value, DictType):
      for k in value:
        cls.build_object(e, k, value[k])
    elif isinstance(value, Entity):
      value = value.to_dict()
      for k in value:
        cls.build_object(e, k, value[k])
    elif isinstance(value, (list, tuple)):
      item_name = inflection.singularize(name)
      for v in value:
        if isinstance(v, (int, float, long)):
          v = unicode(v)
        elif isinstance(v, bool):
          v = unicode(v).lower()
        cls.build_object(parent, item_name, v)
      return
    elif value is not None:
      e.text = unicode(value)
    parent.append(e)
  
  @classmethod
  def build_document(cls, d):
    root = ET.Element(cls.xml_root_name, status=u'ok')
    for k in d:
      cls.build_object(root, k, d[k])
    return root
  

# Only register if an element tree impl is available
if ET is not None:
  # This registers the serializer and enables Smisk and other code to make use
  # of this serializer.
  serializers.register(MyXMLSerializer)
