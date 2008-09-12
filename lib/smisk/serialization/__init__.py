# encoding: utf-8
'''Data serializers'''

try:
  from cStringIO import StringIO
except ImportError:
  from StringIO import StringIO


serializers = {}
'Serializers keyed by lower case MIME types.'


class BaseSerializer(object):
  '''
  Abstract baseclass for serializers
  '''
  
  output_type = 'application/octet-stream'
  '''
  MIME type of output.
  
  Should not include charset.
  
  Serializers register themselves in the module-level dictionary `serializers`
  for any MIME types they can handle. This directive, mime_type, is only used
  for output.
  '''
  
  output_encoding = None
  '''
  Output character encoding
  '''
  
  @classmethod
  def encode(cls, *args, **params):
    """
    :param args: 
    :type  args:   list
    :param params: 
    :type  params: dict
    :rtype:        string
    """
    raise NotImplementedError('%s.encode' % cls.__name__)
  
  @classmethod
  def encode_error(cls, typ, val, tb):
    """
    Encode an error.
    
    Might return None to indicate someone else should handle the error.
    
    :param typ: Error type
    :type  typ: Type
    :param val: Value
    :type  val: object
    :param tb:  Traceback
    :type  tb:  object
    :rtype:     string
    """
    return None
  
  @classmethod
  def decode(cls, file):
    """
    :param file: A file-like object implementing at least the read() method
    :type  file: object
    :rtype:      tuple
    :returns:    A tuple of (string methodname, list args, dict params)
    """
    raise NotImplementedError('%s.decode' % cls.__name__)
  

# Load serializers
import json, xmlrpc, xml_rest
