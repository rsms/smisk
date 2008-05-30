# encoding: utf-8
'''Data serializers'''

try:
  from cStringIO import StringIO
except ImportError:
  from StringIO import StringIO


class Serializer(object):
  """Abstract baseclass for serializers"""
  
  mime_types = ['application/octet-stream']
  '''
  The MIME types for the serial format.
  
  The list must be at least 1 item long.
  The first item is used when producing output.
  All items are tested when interpreting input.
  '''
  
  @classmethod
  def encode(cls, st, file):
    """
    Serialize a structure and write it to file.
    
    :param st:   Structure to be serialized
    :type  st:   object
    :param file: Destination. A file-like object implementing at least the write(string, int) method.
    :type  file: file
    :rtype:      None
    """
    raise NotImplementedError('%s.encode' % cls.__name__)
  
  @classmethod
  def decode(cls, file):
    """
    Extract a previously serialized structure from file.
    
    :param file: A file-like object implementing at least the read() method
    :type  file: file
    :rtype:      object
    """
    raise NotImplementedError('%s.decode' % cls.__name__)
  
  @classmethod
  def encodes(cls, st):
    """
    Serialize a structure and return it as a string.
    
    :param st:   Structure to be serialized
    :type  st:   object
    :rtype:      string
    """
    # Defaults to using StringIO and using encode
    f = StringIO()
    cls.encode(st, f)
    return f.getvalue()
  
  @classmethod
  def decodes(cls, string):
    """
    Extract a previously serialized structure from a string.
    
    :param string: A file-like object implementing at least the read() method
    :type  string: string
    :rtype:        object
    """
    # Defaults to using StringIO and using decode
    return cls.decode(StringIO(string))
  
