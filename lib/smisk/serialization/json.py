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
    from json import dumps as json_encode, loads as json_decode
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
  '''JavaScript Object Notation
  '''
  name = 'JSON'
  extensions = ('json',)
  media_types = ('application/json',)
  charset = 'utf-8'
  can_serialize = True
  can_unserialize = True
  
  @classmethod
  def serialize(cls, params, charset):
    return (cls.charset, json_encode(params))
  
  @classmethod
  def serialize_error(cls, status, params, charset):
    return cls.serialize(params, charset)
  
  @classmethod
  def unserialize(cls, file, length=-1, charset=None):
    # return (list args, dict params)
    if not charset:
      charset = cls.charset
    st = json_decode(file.read(length).decode(charset))
    if isinstance(st, dict):
      return (None, st)
    elif isinstance(st, list):
      return (st, None)
    else:
      return ((st,), None)
  

class JSONPSerializer(JSONSerializer):
  '''JavaScript Object Notation with Padding
  
  JSONP support through passing the special ``callback`` query string parameter.
  '''
  name = 'JSONP'
  extensions = ('js','jsonp')
  media_types = ('text/javascript',)
  
  @classmethod
  def serialize(cls, params, charset):
    callback = u'jsonp_callback'
    if request:
      callback = request.get.get('callback', callback)
    s = '%s(%s);' % (callback.encode(cls.charset), json_encode(params))
    return (cls.charset, s)
  

# Don't register if we did not find a json implementation
if json_encode is not None:
  serializers.register(JSONSerializer)
  serializers.register(JSONPSerializer)

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
