# encoding: utf-8
'''Data codecs

.. packagetree::
.. importgraph::
'''
from StringIO import StringIO

__all__ = [
  'codecs',
  'data', 'CodecRegistry', 'EncodingError', 'DecodingError', 'BaseCodec',
]

class data(str):
  '''Represents arbitrary bytes.
  '''
  def __init__(self, source):
    '''Wrap source as data.
    
    :Parameters:
      source : object
        String or file object. If this is a file object, it will
        be closed automatically.
    '''
    if hasattr(source, 'read'):
      try:
        str.__init__(self, source.read())
      finally:
        source.close()
    else:
      str.__init__(self, source)
  


class CodecRegistry(object):
  first_in = None
  '''First registered codec.
  
  :type: BaseCodec
  '''
  
  media_types = {}
  '''Media type-to-Codec map.
  
  :type: dict
  '''
  
  extensions = {}
  '''Filename extension-to-Codec map.
  
  :type: dict
  '''
  
  codecs = []
  '''List of available codecs.
  
  :type: list
  '''
  
  def register(self, codec):
    '''Register a new codec
    '''
    # Already registered?
    if codec in self.codecs:
      return
    # Register Codec
    self.codecs.append(codec)
    # Register Media types
    for t in codec.media_types:
      if codec.media_type is None:
        codec.media_type = t
      self.media_types[t] = codec
    # Register extensions/formats
    for ext in codec.extensions:
      if codec.extension is None:
        codec.extension = ext
      self.extensions[ext] = codec
    # Set first_in
    if self.first_in is None:
      self.first_in = codec
    codec.did_register(self)
  
  def unregister(self, codec):
    '''Unregister a previously registered codec.
    '''
    for i in range(len(self.codecs)):
      if self.codecs[i] == codec:
        del self.codecs[i]
        break
    for k,v in self.media_types.items():
      if v == codec:
        del self.media_types[k]
    for k,v in self.extensions.items():
      if v == codec:
        del self.extensions[k]
    if self.first_in == codec:
      if self.codecs:
        self.first_in = self.codecs[0]
      else:
        self.first_in = None
    codec.did_unregister(self)
  
  def __iter__(self):
    return self.codecs.__iter__()
  

codecs = CodecRegistry()
'''The codec registry.

:type: Codecs
'''

class EncodingError(Exception):
  '''Indicates an encoding error'''
  pass

class DecodingError(Exception):
  '''Indicates an encoding error'''
  pass


class BaseCodec(object):
  '''
  Abstract baseclass for codecs
  '''
  
  name = 'Untitled codec'
  '''
  A human readable and descriptive but short name of the codec.
  
  :type: string
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
  
  @classmethod
  def directions(cls):
    '''List of possible directions.
    
    :Returns:
      ``["read", "write"]``, ``["read"]``, ``["write"]`` or ``[]``
    :rtype: list'''
    try:
      return cls._directions
    except AttributeError:
      cls._directions = []
      # test decode
      can_read = True
      try:
        cls.decode(StringIO(''), 0)
      except NotImplementedError, e:
        can_read = False
      except:
        pass
      if can_read:
        cls._directions.append('read')
      # test encode
      try:
        if cls.encode({'a':1}, 'utf-8') is not None:
          cls._directions.append('write')
      except NotImplementedError:
        pass
      return cls._directions
  
  @classmethod
  def did_register(cls, registry):
    '''Called when this codec has been successfully registered in a `CodecRegistry`.
    
    Default implementation does nothing. This is meant to be overridden in
    subclasses to allow a kind of *initialization routine*, setting up
    `cls` if needed.
    
    :Parameters:
      registry : CodecRegistry
        The registry in which this codec was just registered
    :rtype: None
    '''
    pass
  
  @classmethod
  def did_unregister(cls, registry):
    '''Called when this codec has been removed from a `CodecRegistry`.
    
    Default implementation does nothing. This is meant to be overridden in
    subclasses to allow a kind of *initialization routine*, tearing down
    `cls` if needed.
    
    :Parameters:
      registry : CodecRegistry
        The registry from which this codec was removed
    :rtype: None
    '''
    pass
  

# Load built-in codecs
import os
from smisk.util import load_modules
load_modules(os.path.dirname(__file__))
