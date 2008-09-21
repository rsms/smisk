# encoding: utf-8
'''Data serializers'''

try:
  from cStringIO import StringIO
except ImportError:
  from StringIO import StringIO


class Serializers(object):
  def __init__(self):
    self.media_types = {}
    self.extensions = {}
  
  def register(self, cls, additional_media_types=[], additional_extensions=[]):
    '''Register a new serializer class'''
    self.media_types[cls.media_type] = cls
    for t in additional_media_types:
      self.media_types[t] = cls
    self.extensions[cls.extension] = cls
    for ext in additional_extensions:
      self.extensions[ext] = cls
  
  def values(self):
    return self.media_types.values()
  

serializers = Serializers()
'Serializers keyed by lower case MIME types.'


class BaseSerializer(object):
  '''
  Abstract baseclass for serializers
  '''
  
  extension = None
  '''Filename extension'''
  
  media_type = 'application/octet-stream'
  '''
  MIME type of output.
  
  Should not include charset.
  
  Serializers register themselves in the module-level dictionary `serializers`
  for any MIME types they can handle. This directive, mime_type, is only used
  for output.
  '''
  
  encoding = None
  '''
  Preferred character encoding
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
import json, xmlrpc, xml, xhtml

# Load unstable serializers
import pickle
