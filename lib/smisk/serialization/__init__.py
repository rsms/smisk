# encoding: utf-8
'''Data serialization

.. packagetree (xxx todo fix for Sphinx)
.. importgraph::
'''
import base64
try:
  import cStringIO as StringIO
except ImportError:
  import StringIO

__all__ = [
  'serializers', # codecs
  'data',
  'Registry', # CodecRegistry
  'SerializationError', # SerializationError
  'UnserializationError', # UnserializationError
  'Serializer', # BaseCodec
]

class data(object):
  '''Represents arbitrary bytes.
  '''
  bytes = None
  ''':type: buffer
  '''
  
  def __init__(self, source):
    '''Wrap source as data.
    
    :Parameters:
      source : object
        String or file object. If this is a file object, it will
        be closed automatically.
    '''
    if hasattr(source, 'read'):
      f = source
      try:
        source = source.read()
      finally:
        f.close()
    self.bytes = buffer(source)
  
  def encode(self):
    '''Return a base-64 encoded representation of this data.
    
    :rtype: string
    '''
    return base64.b64encode(self.bytes)
  
  @classmethod
  def decode(cls, string):
    '''Decode data which is a base-64 encoded string.
    
    :Parameters:
      string : string
        Base-64 encoded data
    :rtype: data
    '''
    return cls(base64.decodestring(string))
  
  def __str__(self):
    return self.bytes or ''
  
  def __cmp__(self, other):
    if isinstance(other, self.__class__):
      other = other.bytes
    return cmp(self.bytes, other)
  
  def __len__(self):
    return len(self.bytes)
  
  def __repr__(self):
    return '<read-only %s.%s, %d bytes at 0x%x>' %\
      (self.__class__.__module__, self.__class__.__name__, len(self.bytes), id(self))
  
  def __str__(self):
    return self.bytes.__str__()
  

class Registry(object):
  first_in = None
  '''First registered serializer.
  
  :type: Serializer
  '''
  
  media_types = {}
  '''Media type-to-Serializer map.
  
  :type: dict
  '''
  
  extensions = {}
  '''Filename extension-to-Serializer map.
  
  :type: dict
  '''
  
  serializers = []
  '''List of available serializers.
  
  :type: list
  '''
  
  def register(self, serializer):
    '''Register a new Serializer
    '''
    # Already registered?
    if serializer in self.serializers:
      return
    # Register Serializer
    self.serializers.append(serializer)
    # Register Media types
    for t in serializer.media_types:
      t = intern(t)
      if serializer.media_type is None:
        serializer.media_type = t
      self.media_types[t] = serializer
    # Register extensions/formats
    for ext in serializer.extensions:
      ext = intern(ext)
      if serializer.extension is None:
        serializer.extension = ext
      self.extensions[ext] = serializer
    # Set first_in
    if self.first_in is None:
      self.first_in = serializer
    serializer.did_register(self)
  
  def unregister(self, serializer):
    '''Unregister a previously registered serializer.
    '''
    for i in range(len(self.serializers)):
      if self.serializers[i] == serializer:
        del self.serializers[i]
        break
    for k,v in self.media_types.items():
      if v == serializer:
        del self.media_types[k]
    for k,v in self.extensions.items():
      if v == serializer:
        del self.extensions[k]
    if self.first_in == serializer:
      if self.serializers:
        self.first_in = self.serializers[0]
      else:
        self.first_in = None
    serializer.did_unregister(self)
  
  def __iter__(self):
    return self.serializers.__iter__()
  

serializers = Registry()
'''The serializer registry.

:type: Registry
'''

class SerializationError(Exception):
  '''Indicates an encoding error'''
  pass

class UnserializationError(Exception):
  '''Indicates an encoding error'''
  pass


class Serializer(object):
  '''Abstract baseclass for serializers
  '''
  
  name = 'Untitled serializer'
  '''A human readable short and descriptive name of the serializer.
  
  :type: string
  '''
  
  extension = None
  '''Primary filename extension.
  
  This is set by ``serializers.register``. You should define your extensions in `extensions`.
  
  :type: string'''
  
  media_type = None
  '''Primary media type.
  
  This is set by ``serializer.register``. You should define your types in `media_types`.
  
  serializers register themselves in the module-level dictionary `serializers`
  for any MIME types they can handle. This directive, mime_type, is only used
  for output.
  
  :type: string
  '''
  
  extensions = tuple()
  '''Filename extensions this serializer can handle.
  
  The first item will be assigned to `extension` and used as primary extension.
  
  :type: collection
  '''
  
  media_types = tuple()
  '''Media types this serializer can handle.
  
  The first item will be assigned to `media_type` and used as primary media type.
  
  :type: collection
  '''
  
  charset = None
  '''Preferred character encoding.
  
  :type: string
  '''
  
  unicode_errors = 'replace'
  '''How to handle unicode conversions.
  
  Possible values: ``strict, ignore, replace, xmlcharrefreplace, backslashreplace``
  
  :type: string
  '''
  
  @classmethod
  def serialize(cls, params, charset):
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
  def serialize_error(cls, status, params, charset):
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
    return cls.serialize(params, charset)
  
  @classmethod
  def unserialize(cls, file, length=-1, charset=None):
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
        cls.unserialize(StringIO(''), 0)
      except NotImplementedError, e:
        can_read = False
      except:
        pass
      if can_read:
        cls._directions.append('read')
      # test encode
      try:
        if cls.serialize({'a':1}, 'utf-8') is not None:
          cls._directions.append('write')
      except NotImplementedError:
        pass
      return cls._directions
  
  @classmethod
  def did_register(cls, registry):
    '''Called when this serializer has been successfully registered in a `Registry`.
    
    Default implementation does nothing. This is meant to be overridden in
    subclasses to allow a kind of *initialization routine*, setting up
    `cls` if needed.
    
    :Parameters:
      registry : Registry
        The registry in which this serializer was just registered
    :rtype: None
    '''
    pass
  
  @classmethod
  def did_unregister(cls, registry):
    '''Called when this serializer has been removed from a `Registry`.
    
    Default implementation does nothing. This is meant to be overridden in
    subclasses to allow a kind of *initialization routine*, tearing down
    `cls` if needed.
    
    :Parameters:
      registry : Registry
        The registry from which this serializer was removed
    :rtype: None
    '''
    pass
  

# Load built-in serializers
import os
from smisk.util.python import load_modules
load_modules(os.path.dirname(__file__))
