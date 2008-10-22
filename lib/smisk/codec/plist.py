# encoding: utf-8
'''XML Property List serialization
'''
import re, logging
from smisk.codec import codecs, data, BaseCodec, EncodingError

try:
  import base64
  from datetime import datetime
  from xml.etree import ElementTree
  from types import *
  Element = ElementTree.Element
except ImportError:
  # xml.etree only available in Python >=2.5
  ElementTree = None

log = logging.getLogger(__name__)

__all__ = [
  'PlistBuildError',
  'XMLPlistETreeBuilder',
  'PlistParseError',
  'XMLPlistETreeParser',
  'XMLPlistETreeCodec']

class PlistBuildError(Exception):
  pass

class XMLPlistETreeBuilder(object):
  '''Builds XML Property Lists using an element tree parser.
  '''
  
  DOCTYPE = u'<?xml version="1.0" encoding="%s"?>\n'\
    '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '\
    '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
  '''XML declaration and document type.
  '''
  
  VERSION = '1.0'
  '''Property List version.
  '''
  
  @classmethod
  def write(cls, obj, destination, encoding='utf-8', doctype=True):
    '''Build and write a XML Property List to `destination`.
    
    :Parameters:
      obj : object
        Python object
      destination : object
        Filename or file object
      encoding : string
        Character encoding
      doctype : bool
        Include xml declaration and doctype
    :rtype: None
    '''
    et = ElementTree.ElementTree(cls.build_tree(obj))
    if doctype:
      destination.write(cls.DOCTYPE % encoding)
    et.write(destination, encoding)
  
  @classmethod
  def build(cls, obj, encoding='utf-8', doctype=True):
    '''Build a XML Property List.
    
    :Parameters:
      obj : object
        Python object
      encoding : string
        Character encoding
      doctype : bool
        Include xml declaration and doctype
    :Returns:
      XML Property List representing `obj`
    :rtype: string
    '''
    s = ElementTree.tostring(cls.build_tree(obj), encoding)
    if doctype:
      return (cls.DOCTYPE % encoding) + s
    return s
  
  @classmethod
  def build_tree(cls, obj):
    '''Build an element tree.
    
    :Parameters:
      obj : object
        Python object
    :Returns:
      Element tree representing `obj`
    :rtype: xml.etree.Element
    '''
    tree = Element('plist', version=cls.VERSION)
    if obj is not None:
      tree.append(cls.build_plist_object(obj))
    return tree
  
  @classmethod
  def build_plist_object(cls, obj):
    if obj is True:
      return Element('true')
    elif obj is False:
      return Element('false')
    elif isinstance(obj, list):
      return cls._array(obj)
    elif isinstance(obj, data): # must be tested before basestr
      return cls._telem('data', base64.b64encode(obj))
    elif isinstance(obj, datetime):
      return cls._telem('date', obj.strftime('%Y-%m-%dT%H:%M:%SZ'))
    elif isinstance(obj, dict):
      return cls._dict(obj)
    elif isinstance(obj, float):
      return cls._telem('real', obj.__str__())
    elif isinstance(obj, int):
      return cls._telem('integer', obj.__str__())
    elif isinstance(obj, basestring):
      return cls._telem('string', obj)
    else:
      raise PlistBuildError('%s not supported' % type(obj).__name__)
  
  @classmethod
  def _telem(cls, name, text):
    e = Element(name)
    e.text = text
    return e
  
  @classmethod
  def _array(cls, obj):
    e = Element('array')
    for o in obj:
      e.append(cls.build_plist_object(o))
    return e
  
  @classmethod
  def _dict(cls, obj):
    e = Element('dict')
    for key, value in obj.iteritems():
      e.append(cls._telem('key', key))
      e.append(cls.build_plist_object(value))
    return e
  

class PlistParseError(Exception):
  pass

class XMLPlistETreeParser(object):
  '''Parses XML Property List using an element tree parser.
  '''
  
  _HANDLERS = None
  
  @classmethod
  def parse(cls, source):
    '''Parse a XML Property List.
    
    :Parameters:
      source : object
        Filename or file object containing XML data.
    :Returns:
      Python object representing `source`
    :rtype: object
    '''
    return cls.parse_document(ElementTree.parse(source).getroot())
  
  @classmethod
  def parse_string(cls, string):
    '''Parse a XML Property List from a string constant.
    
    :Parameters:
      string : string
        A string containing XML data.
    :Returns:
      Python object representing `string`
    :rtype: object
    '''
    return cls.parse_document(ElementTree.fromstring(string))
  
  @classmethod
  def parse_document(cls, doc):
    '''Parse a element tree document.
    
    :Parameters:
      doc : xml.etree.Element
        An etree Element
    :Returns:
      Python object representing `doc`
    :rtype: object
    '''
    if not cls._HANDLERS:
      cls._HANDLERS = dict((name, getattr(cls, 'parse_plist_' + name))
         for name in 'array data date dict real integer string true false'.split())
    return cls.parse_plist_object(doc.getchildren()[0])
  
  @classmethod
  def parse_plist_object(cls, elem):
    try:
      return cls._HANDLERS[elem.tag](elem)
    except KeyError:
      raise PlistParseError('%s not supported' % elem.tag)
  
  @classmethod
  def parse_plist_array(cls, elem):
    return [cls.parse_plist_object(child) for child in elem.getchildren()]
  
  @classmethod
  def parse_plist_data(cls, elem):
    return  base64.b64decode(elem.text)
  
  @classmethod
  def parse_plist_date(cls, elem):
    return datetime.datetime.strptime(elem.text, '%Y-%m-%dT%H:%M:%SZ')
  
  @classmethod
  def parse_plist_dict(cls, elem):
    children = elem.getchildren()
    
    if len(children) % 2 != 0:
      raise PlistParseError('dict must have even childrens')
    
    dic = dict()
    for i in xrange(len(children) / 2):
      key = children[i * 2]
      value = children[i * 2 + 1]
  
      if key.tag != 'key': raise PlistParseError('key element not found')
      dic[key.text] = cls.parse_plist_object(value)
    
    return dic
  
  @classmethod
  def parse_plist_real(cls, elem):
    return float(elem.text)
  
  @classmethod
  def parse_plist_integer(cls, elem):
    return int(elem.text)
  
  @classmethod
  def parse_plist_string(cls, elem):
    return elem.text
  
  @classmethod
  def parse_plist_true(cls, elem):
    return True
  
  @classmethod
  def parse_plist_false(cls, elem):
    return False
  


class XMLPlistETreeCodec(BaseCodec):
  '''XML Property List codec'''
  
  name = 'XML Property List'
  extensions = ('plist',)
  media_types = ('application/plist+xml',)
  charset = 'utf-8'
  
  @classmethod
  def encode(cls, params, charset):
    return (charset, XMLPlistETreeBuilder.build(params, charset).encode(charset))
  
  @classmethod
  def decode(cls, f, f_len=-1, charset=None):
    # return (list args, dict params)
    st = XMLPlistETreeParser.parse_string(f.read(f_len))
    if isinstance(st, dict):
      return (None, st)
    elif isinstance(st, list):
      return (st, None)
    else:
      return ((st,), None)
  

if ElementTree is not None:
  codecs.register(XMLPlistETreeCodec)

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
