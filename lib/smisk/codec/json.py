# encoding: utf-8
'''
JSON: JavaScript Object Notation

:see: `RFC 4627 <http://tools.ietf.org/html/rfc4627>`__
:requires: `cjson <http://pypi.python.org/pypi/python-cjson>`__ | minjson
'''
from smisk.core import Application
from smisk.codec import codecs, BaseCodec
try:
  from cjson import encode as json_encode, decode as json_decode,\
                    DecodeError, EncodeError
except ImportError:
  try:
    from minjson import write as json_encode, read as json_decode,\
                        ReadException as DecodeError,\
                        WriteException as EncodeError
  except ImportError:
    json_encode = None
    from warnings import warn
    warn('No JSON implementation available. Install cjson or minjson.')

class codec(BaseCodec):
  '''JSON with JSONP support.
  
  JSONP support through passing the special ``callback`` query string parameter.
  '''
  name = 'JSON: JavaScript Object Notation'
  extensions = ('json',)
  media_types = ('application/json',)
  
  @classmethod
  def encode(cls, params, charset):
    callback = None
    if Application.current:
      callback = Application.current.request.get.get('callback', None)
    if callback:
      return (None, '%s(%s);' % (callback, json_encode(params)))
    else:
      return (None, json_encode(params))
  
  @classmethod
  def encode_error(cls, status, params, charset):
    return (None, json_encode(params))
  
  @classmethod
  def decode(cls, file, length=-1, charset=None):
    # return (list args, dict params)
    st = json_decode(file.read(length))
    if isinstance(st, dict):
      return (None, st)
    elif isinstance(st, list):
      return (st, None)
    else:
      return ((st,), None)
  

# Don't register if we did not find a json implementation
if json_encode is not None:
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
  }, None)
  print s