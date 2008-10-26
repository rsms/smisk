# encoding: utf-8
'''PHP serial serialization
'''
from smisk.serialization import *
from types import *
try:
  from cStringIO import StringIO
except:
  from StringIO import StringIO

class PHPSerialSerializationError(SerializationError):
  pass

class PHPSerialSerializer(Serializer):
  '''PHP serial serializer.'''
  name = 'PHP serial'
  extensions = ('phpser',)
  media_types = ('application/php', 'application/vnd.php.serialized')
  
  @classmethod
  def encode_key(cls, obj, f):
    if isinstance(obj, (IntType, FloatType, LongType, BooleanType)):
      f.write('i:%d;' % int(obj))
    elif isinstance(obj, basestring):
      try:
        f.write('i:%d;' % int(obj))
      except ValueError:
        f.write('s:%d:"%s";' % (len(obj), obj))
    elif isinstance(obj, NoneType):
      f.write('s:0:"";')
    else:
      raise PHPSerialSerializationError('Unsupported type: %s' % type(obj).__name__)
  
  @classmethod
  def encode_object(cls, obj, f):
    if isinstance(obj, BooleanType):
      f.write('b:%d;' % obj)
    elif isinstance(obj, (FloatType, LongType)):
      f.write('d:%s;' % obj)
    elif isinstance(obj, IntType):
      f.write('i:%d;' % obj)
    elif isinstance(obj, data):
      f.write('s:%d:"%s";' % (len(obj), obj))
    elif isinstance(obj, basestring):
      try:
        f.write('i:%d;' % int(obj))
      except ValueError:
        f.write('s:%d:"%s";' % (len(obj), obj))
    elif isinstance(obj, NoneType):
      f.write('N;')
    elif isinstance(obj, (ListType, TupleType)):
      f.write('a:%i:{' % len(obj))
      for k,v in enumerate(obj):
        f.write('i:%d;' % k)
        cls.encode_object(v, f)
      f.write('}')
    elif isinstance(obj, DictType):
      f.write('a:%i:{' % len(obj))
      for k,v in obj.iteritems():
        cls.encode_key(k, f)
        cls.encode_object(v, f)
      f.write('}')
    else:
      raise PHPSerialSerializationError('Unsupported type: %s' % type(obj).__name__)
  
  @classmethod
  def serialize(cls, params, charset):
    f = StringIO()
    cls.encode_object(params, f)
    return (None, f.getvalue())
  

serializers.register(PHPSerialSerializer)

if __name__ == '__main__':
  from datetime import datetime
  print PHPSerialSerializer.serialize({
    'message': 'Hello worlds',
    'internets': [
      'interesting',
      'lolz',
      42.0,
      {
        'tubes': [1,3,16,18,24],
        'persons': True,
        'me again': {
          'message': 'Hello worlds',
          'internets': [
            'interesting',
            'lolz',
            42.0,
            {
              'tubes': [1,3,16,18,24],
              'persons': True
            }
          ],
          'today': str(datetime.now())
        }
      }
    ],
    'today': str(datetime.now())
  }, 'whatever')[1]