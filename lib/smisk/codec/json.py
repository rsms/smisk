# encoding: utf-8
'''
JSON serialization (RFC 4627)
'''
from smisk.codec import codecs, BaseCodec
try:
  from cjson import encode, decode, DecodeError, EncodeError
except ImportError:
  try:
    from minjson import write as encode, read as decode
    from minjson import ReadException as DecodeError, WriteException as EncodeError
  except ImportError:
    encode = None
    from warnings import warn, showwarning
    warn('No JSON implementation available. Install cjson or minjson.')

class codec(BaseCodec):
  '''JSON codec'''
  extensions = ('json',)
  media_types = ('application/json', 'application/x-json')
  
  @classmethod
  def encode(cls, params, charset):
    return (None, encode(params))
  
  @classmethod
  def encode_error(cls, status, params, charset):
    return (None, encode(**params))
  
  @classmethod
  def decode(cls, file, length=-1, charset=None):
    # return (list args, dict params)
    st = decode(file.read(length))
    if isinstance(st, dict):
      return (None, st)
    elif isinstance(st, list):
      return (st, None)
    else:
      return ((st,), None)
  

# Don't register if we did not find a json implementation
if encode is not None:
  codecs.register(codec)

if __name__ == '__main__':
  s = codec.encode({
    'message': 'Hello worlds',
    'internets': [
      'interesting',
      'lolz',
      42.0,
      {
        'tubes': [1,3,16,18,24],
        'persons': True,
        'me agåain': {
          'message': 'Hello worlds',
          'internets': [
            'interesting',
            'lolz',
            42.0,
            {
              'tubes': [1,3,16,18,24],
              'persons': True
            }
          ]
        }
      }
    ]
  }, codec.charset)
  print s