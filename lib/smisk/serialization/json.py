# encoding: utf-8
'''
JSON: JavaScript Object Notation

:see: `RFC 4627 <http://tools.ietf.org/html/rfc4627>`__
:requires: `cjson <http://pypi.python.org/pypi/python-cjson>`__ | minjson
'''
from smisk.core import request
from smisk.serialization import serializers, Serializer
try:
  from cjson import \
              encode as json_encode,\
              decode as json_decode,\
              DecodeError,\
              EncodeError
except ImportError:
  try:
    from minjson import \
               write as json_encode,\
                read as json_decode,\
       ReadException as DecodeError,\
      WriteException as EncodeError
  except ImportError:
    json_encode = None

class JSONSerializer(Serializer):
  '''JSON with JSONP support.
  
  JSONP support through passing the special ``callback`` query string parameter.
  '''
  name = 'JSON: JavaScript Object Notation'
  extensions = ('json',)
  media_types = ('application/json',)
  
  @classmethod
  def serialize(cls, params, charset):
    callback = None
    if request:
      callback = request.get.get('callback', None)
    if callback:
      return (None, '%s(%s);' % (callback, json_encode(params)))
    else:
      return (None, json_encode(params))
  
  @classmethod
  def serialize_error(cls, status, params, charset):
    return (None, json_encode(params))
  
  @classmethod
  def unserialize(cls, file, length=-1, charset=None):
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
  serializers.register(JSONSerializer)

if __name__ == '__main__':
  s = JSONSerializer.serialize({
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
