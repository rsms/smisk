# encoding: utf-8
'''Data serializers'''

try:
  from cStringIO import StringIO
except ImportError:
  from StringIO import StringIO


class Serializers(object):
  first_in = None
  """First registered serializer"""
  
  def __init__(self):
    self.media_types = {}
    self.extensions = {}
  
  def register(self, cls):
    '''Register a new serializer class'''
    # Register Media types
    for t in cls.media_types:
      if cls.media_type is None:
        cls.media_type = t
      self.media_types[t] = cls
    # Register extensions/formats
    for ext in cls.extensions:
      if cls.extension is None:
        cls.extension = ext
      self.extensions[ext] = cls
    # Set first_in
    if self.first_in is None:
      self.first_in = cls
  
  def values(self):
    return self.media_types.values()
  

serializers = Serializers()
'Serializers keyed by lower case MIME types.'


class BaseSerializer(object):
  '''
  Abstract baseclass for serializers
  '''
  
  extension = None
  '''
  Primary filename extension.
  
  This is set by Serializers.register. You should define your types in `media_types`.
  
  :type: string'''
  
  media_type = None
  '''
  Primary media type.
  
  This is set by Serializers.register. You should define your types in `media_types`.
  
  Serializers register themselves in the module-level dictionary `serializers`
  for any MIME types they can handle. This directive, mime_type, is only used
  for output.
  
  :type: string
  '''
  
  extensions = tuple()
  '''
  Filename extensions this serializer can handle.
  
  The first item will be assigned to `extension` and used as primary extension.
  
  :type: collection
  '''
  
  media_types = tuple()
  '''
  Media types this serializer can handle.
  
  The first item will be assigned to `media_type` and used as primary media type.
  
  :type: collection
  '''
  
  encoding = None
  '''
  Preferred character encoding.
  
  :type: string
  '''
  
  @classmethod
  def encode(cls, **params):
    '''
    :param params: 
    :type  params: dict
    :rtype:        string
    '''
    raise NotImplementedError('%s.encode' % cls.__name__)
  
  @classmethod
  def encode_error(cls, status, params, typ, val, tb):
    '''
    Encode an error.
    
    Might return None to indicate someone else should handle the error.
    
    :param status: HTTP status
    :type  status: smisk.mvc.http.Status
    :param params: Parameters
    :type  params: dict
    :param typ:    Error type
    :type  typ:    Type
    :param val:    Value
    :type  val:    object
    :param tb:     Traceback
    :type  tb:     object
    :rtype: string
    '''
    return None
  
  @classmethod
  def decode(cls, file, length=-1):
    '''
    :param file: A file-like object implementing at least the read() method
    :type  file: object
    :returns:    2-tuple of (list args, dict params) args and params might be None
    :rtype:      tuple
    '''
    raise NotImplementedError('%s.decode' % cls.__name__)
  
  @classmethod
  def add_content_type_header(cls, response):
    '''Adds "Content-Type" header if missing'''
    if response.find_header('Content-Type:') == -1:
      if cls.encoding is not None:
        response.headers.append('Content-Type: %s; charset=%s' % (cls.media_type, cls.encoding))
      else:
        response.headers.append('Content-Type: %s' % cls.media_type)
  

# Load serializers
import json, xmlrpc, xml, xhtml, plist, text

# Load unstable serializers
import pickle
