# encoding: utf-8
'''Data serialization
'''
import base64, logging
try:
  from cStringIO import StringIO
except ImportError:
  from StringIO import StringIO

log = logging.getLogger(__name__)

__all__ = [
  'serializers', # codecs
  'data',
  'Registry', # CodecRegistry
  'SerializationError', # SerializationError
  'UnserializationError', # UnserializationError
  'Serializer' # BaseCodec
]

import plistlib_
plistlib_.Data.encode = plistlib_.Data.asBase64
plistlib_.Data.decode = plistlib_.Data.fromBase64

class data(plistlib_.Data):
  '''Represents arbitrary bytes.
  '''
  def __init__(self, source):
    if hasattr(source, 'read'):
      self.data = source.read()
    else:
      self.data = str(source)
  
  encode = plistlib_.Data.asBase64
  decode = plistlib_.Data.fromBase64
  
  def __len__(self):
    return len(self.data)
  
  def __str__(self):
    return self.data.__str__()
  

class Registry(object):
  first_in = None
  '''First registered serializer.
  '''
  
  media_types = {}
  '''Media type-to-Serializer map.
  '''
  
  extensions = {}
  '''Filename extension-to-Serializer map.
  '''
  
  serializers = []
  '''List of available serializers.
  '''
  
  def register(self, serializer):
    '''Register a new Serializer
    '''
    # Already registered?
    if serializer in self.serializers:
      log.debug('skipped registering already registered serializer %r', serializer)
      return
    log.debug('registering serializer %r', serializer)
    # Check basics
    if not isinstance(serializer.media_types, (tuple, list)):
      raise TypeError('media_types attribute of %r must be a tuple or a list '\
        'of strings' % serializer)
    if not isinstance(serializer.extensions, (tuple, list)):
      raise TypeError('extensions attribute of %r must be a tuple or a list '\
        'of strings' % serializer)
    # Register Serializer
    self.serializers.append(serializer)
    # Register Media types
    for t in serializer.media_types:
      self.media_types[intern(t.lower())] = serializer
    # Register extensions/formats
    for ext in serializer.extensions:
      self.extensions[intern(ext.lower())] = serializer
    # Set first_in
    if self.first_in is None:
      self.first_in = serializer
    serializer.did_register(self)
  
  def unregister(self, serializer=None):
    '''Unregister a previously registered serializer or all registered
    serializers, if `serializer` is `None`.
    '''
    if serializer is None:
      # Unreg all
      for s in self.serializers:
        s.did_unregister(self)
      self.media_types = {}
      self.extensions = {}
      self.serializers = []
    else:
      # Unreg specific
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
  
  def find(self, media_type_or_extension):
    '''Find a serializer associated with a media type or an extension.
    Returns None if not found.
    '''
    key = intern(media_type_or_extension.lower())
    try:
      return self.media_types[key]
    except KeyError:
      try:
        return self.extensions[key]
      except KeyError:
        pass
  
  def associate(self, serializer, media_type=None, extension=None, override_existing=True):
    '''Associate a serializer with formats and extensions
    '''
    if serializer not in self.serializers:
      raise LookupError('serializer %r is not yet registered' % serializer)
    
    if media_type is None:
      media_type = []
    elif not isinstance(media_type, (list, tuple)):
      media_type = [media_type]
    
    if extension is None:
      extension = []
    elif not isinstance(extension, (list, tuple)):
      extension = [extension]
    
    for t in media_type:
      t = intern(t.lower())
      if not override_existing and self.media_types.get(t, None) is not serializer:
        raise Exception('media type %r is already associated with another serializer' % t)
      self.media_types[t] = serializer
    
    for ext in extension:
      ext = intern(ext.lower())
      if not override_existing and self.extensions.get(ext, None) is not serializer:
        raise Exception('extension %r is already associated with another serializer' % ext)
      self.extensions[ext] = serializer
  
  @property
  def readers(self):
    '''Iterate serializers able to read, or unserialize, data.
    '''
    for ser in self.serializers:
      if 'read' in ser.directions():
        yield ser
  
  @property
  def writers(self):
    '''Iterate serializers able to write, or serialize, data.
    '''
    for ser in self.serializers:
      if 'write' in ser.directions():
        yield ser
  
  def __iter__(self):
    return self.serializers.__iter__()
  
  def __contains__(self, item):
    return self.serializers.__contains__(item)
  
  def __getitem__(self, key):
    return self.serializers.__getitem__(key)
  
  def __len__(self):
    return self.serializers.__len__()
  

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
  '''
  
  extensions = tuple()
  '''Filename extensions this serializer can handle.
  '''
  
  media_types = tuple()
  '''Media types this serializer can handle.
  '''
  
  charset = None
  '''Preferred character encoding.
  '''
  
  unicode_errors = 'strict'
  '''How to handle unicode conversions.
  '''
  
  handles_empty_response = False
  '''If enabled, serialize() will be called even when leafs does not generate payloads.
  '''
  
  can_serialize = False
  '''Declares where there or not this serializer can write/encode/serialize data.
  '''
  
  can_unserialize = False
  '''Declares where there or not this serializer can read/decode/unserialize data.
  '''
  
  @classmethod
  def serialize(cls, params, charset):
    # should return tuple(str charset, str data)
    raise NotImplementedError('%s.encode' % cls.__name__)
  
  @classmethod
  def serialize_error(cls, status, params, charset):
    # should return tuple(str charset, str data)
    return cls.serialize(params, charset)
  
  @classmethod
  def unserialize(cls, file, length=-1, charset=None):
    # should return tuple(list args, dict params)
    raise NotImplementedError('%s.decode' % cls.__name__)
  
  @classmethod
  def add_content_type_header(cls, response, charset):
    p = response.find_header('Content-Type:')
    if p != -1:
      if charset and 'charset=' not in response.headers[p]:
        response.headers[p] = response.headers[p] + '; charset=' + charset
    else:
      if charset:
        response.headers.append('Content-Type: %s; charset=%s' % (cls.media_types[0], charset))
      else:
        response.headers.append('Content-Type: %s' % cls.media_types[0])
  
  _DIR_RW = ['read','write']
  _DIR_R = ['read']
  _DIR_W = ['write']
  _DIR_ = []
  
  @classmethod
  def directions(cls):
    '''Read/write capabilities.
    '''
    if cls.can_serialize and cls.can_unserialize:
      return cls._DIR_RW
    elif cls.can_serialize:
      return cls._DIR_W
    elif cls.can_unserialize:
      return cls._DIR_R
    return cls._DIR_
  
  @classmethod
  def did_register(cls, registry):
    '''Called when this serializer has been successfully registered in a `Registry`.
    '''
    pass
  
  @classmethod
  def did_unregister(cls, registry):
    '''Called when this serializer has been removed from a `Registry`.
    '''
    pass
  
