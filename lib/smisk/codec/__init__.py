# encoding: utf-8
'''Data codecs'''

class Codecs(object):
  first_in = None
  """First registered codec"""
  
  def __init__(self):
    self.media_types = {}
    self.extensions = {}
  
  def register(self, cls):
    '''Register a new codec class'''
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
  

codecs = Codecs()
'codecs keyed by lower case MIME types.'


class BaseCodec(object):
  '''
  Abstract baseclass for codecs
  '''
  
  extension = None
  '''
  Primary filename extension.
  
  This is set by codecs.register. You should define your extensions in `extensions`.
  
  :type: string'''
  
  media_type = None
  '''
  Primary media type.
  
  This is set by codecs.register. You should define your types in `media_types`.
  
  codecs register themselves in the module-level dictionary `codecs`
  for any MIME types they can handle. This directive, mime_type, is only used
  for output.
  
  :type: string
  '''
  
  extensions = tuple()
  '''
  Filename extensions this codec can handle.
  
  The first item will be assigned to `extension` and used as primary extension.
  
  :type: collection
  '''
  
  media_types = tuple()
  '''
  Media types this codec can handle.
  
  The first item will be assigned to `media_type` and used as primary media type.
  
  :type: collection
  '''
  
  charset = None
  '''
  Preferred character encoding.
  
  :type: string
  '''
  
  @classmethod
  def encode(cls, params, charset):
    '''
    :param params:    Parameters
    :type  params:    dict
    :param charset:   Destination charset. Might be discarded, so care about the returned charset.
    :type  charset:   string
    :returns:         Tuple of (charset, string data) where charset is the name of the
                      actual charset used and might be None if binary or unknown.
    :rtype:           tuple
    '''
    raise NotImplementedError('%s.encode' % cls.__name__)
  
  @classmethod
  def encode_error(cls, status, params, charset):
    '''
    Encode an error.
    
    Might return None to indicate that someone else should handle the error encoding.
    
    `params` will always contain:
      * "name":         string  Name of the error. i.e. "Not Found"
      * "code":         int     Error code. i.e. 404
      * "description":  string  Description of the error.
      * "traceback":    object  A list of strings or None if not available.
      * "server":       string  Short one line description of the server name, port and software.
    
    :param status:    HTTP status
    :type  status:    smisk.mvc.http.Status
    :param params:    Parameters
    :type  params:    dict
    :param charset:   Destination charset. Might be discarded, so care about the returned charset.
    :type  charset:   string
    :returns:         Tuple of (charset, string data) where charset is the name of the
                      actual charset used and might be None if binary or unknown.
    :rtype:           tuple
    '''
    return cls.encode(params, charset)
  
  @classmethod
  def decode(cls, file, length=-1, charset=None):
    '''
    :param file:      A file-like object implementing at least the read() method
    :type  file:      object
    :param length:
    :type  length:    int
    :param charset:
    :type  charset:   string
    :returns:         Tuple of (list args, dict params) args and params might be None
    :rtype:           tuple
    '''
    raise NotImplementedError('%s.decode' % cls.__name__)
  
  @classmethod
  def add_content_type_header(cls, response, charset):
    '''Adds "Content-Type" header if missing'''
    if response.find_header('Content-Type:') == -1:
      if charset is not None:
        response.headers.append('Content-Type: %s; charset=%s' % (cls.media_type, charset))
      else:
        response.headers.append('Content-Type: %s' % cls.media_type)
  

# Load built-in codecs
import os
from smisk.util import load_modules_in_dir
load_modules_in_dir(os.path.dirname(__file__))
