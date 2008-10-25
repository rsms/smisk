# encoding: utf-8
'''XML support.
'''
import logging
from smisk.codec import codecs, data, BaseCodec
from smisk.core import Application

try:
  from xml.etree import ElementTree
  Element = ElementTree.Element
except ImportError:
  # xml.etree only available in Python >=2.5
  ElementTree = None
  Element = None

log = logging.getLogger(__name__)

__all__ = ['codecs', 'data', 'XMLBaseCodec', 'ElementTree', 'Element']


class XMLBaseCodec(BaseCodec):
  '''XML codec baseclass.
  
  Baseclass for XML codecs.
  '''
  name = 'XML'
  charset = 'utf-8'
  
  xml_declaration = '<?xml version="1.0" encoding="%s"?>\n'
  ''':type: string
  '''
  
  xml_doctype = None
  '''Document type (Doctype) specifier.
  
  :type: string
  '''
  
  xml_default_ns = None
  ''':type: string
  '''
  
  xml_root_name = None
  '''Name of root element, if any.
  
  :type: string
  '''
  
  xml_root_attrs = {}
  ''':type: dict
  '''
  
  @classmethod
  def parse_object(cls, elem):
    '''Parse an Element, potentially representing a Python object.
    
    You must implement this method in order to enable decoding.
    
    :Parameters:
      elem : xml.etree.Element
        Element
    :rtype: object
    '''
    raise NotImplementedError('%s.parse_object()' % cls.__name__)
  
  @classmethod
  def build_object(cls, obj):
    '''Parse an object, potentially representing an element in a XML document.
    
    You must implement this method in order to enable encoding.
    
    :Parameters:
      obj : object
        Python object
    :rtype: xml.etree.Element
    '''
    raise NotImplementedError('%s.build_object()' % cls.__name__)
  
  @classmethod
  def parse_document(cls, elem):
    '''Parse an element tree.
    
    :Parameters:
      elem : xml.etree.Element
        Document root element
    :rtype: object
    '''
    if cls.xml_root_name:
      elem = elem.getchildren()[0]
    return cls.parse_object(elem)
  
  @classmethod
  def build_document(cls, obj):
    '''Build an element tree.
    
    :Parameters:
      obj : object
        Python object
    :rtype: xml.etree.Element
    '''
    if not cls.xml_root_name:
      return cls.build_object(obj)
    else:
      if cls.xml_default_ns is not None:
        root = Element(cls.xml_root_name, xmlns=cls.xml_default_ns, **cls.xml_root_attrs)
      else:
        root = Element(cls.xml_root_name, **cls.xml_root_attrs)
      if obj is not None:
        root.append(cls.build_object(obj))
      return root
  
  @classmethod
  def encode(cls, params, charset):
    doc = cls.build_document(params)
    if cls.xml_declaration:
      string = (cls.xml_declaration % charset)
    else:
      string = ''
    if cls.xml_doctype:
      string += cls.xml_doctype
    string += ElementTree.tostring(doc, charset).encode(charset)
    return (charset, string)
  
  @classmethod
  def decode(cls, file, length=-1, charset=None):
    # return (list args, dict params)
    st = cls.parse_document(ElementTree.fromstring(file.read(length)))
    if isinstance(st, dict):
      return (None, st)
    elif isinstance(st, list):
      return (st, None)
    else:
      return ((st,), None)
  
  @classmethod
  def xml_tag(cls, elem):
    '''Returns the tag name and namespace, if any.
    
    :Parameters:
      elem : xml.etree.Element
        The element
    :returns: A tuple of (string name, string namespace or None)
    :rtype: tuple
    '''
    name = elem.tag
    ns = None
    p = name.find('}')
    if p != -1:
      ns = name[1:p]
      name = name[p+1:]
    return name, ns
  
  @classmethod
  def xml_mktext(cls, name, text, **attributes):
    '''Helper to create an element with text value.
    
    :Parameters:
      name : string
        Element name
      text : string
        Text value
    :rtype: xml.etree.Element
    '''
    e = Element(name, **attributes)
    e.text = text
    return e

if __name__ == '__main__':
  print XMLPlistETreeCodec.encode({
    'message': 'Hello worlds',
    'internets': [
      'interesting',
      'lolz',
      42.0,
      {
        'tubes': [1,3,16,18,24],
        'persons': True
      }
    ],
    'today': datetime.now()
  }, charset='utf-8')
