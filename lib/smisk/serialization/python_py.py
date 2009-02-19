# encoding: utf-8
'''Python repr serialization.
'''
from smisk.serialization import serializers, Serializer

class PythonPySerializer(Serializer):
  '''Plain Python code
  '''
  name = 'Python repr'
  extensions = ('py',)
  media_types = ('text/x-python',)
  can_serialize = True
  can_unserialize = True
  
  @classmethod
  def serialize(cls, params, charset):
    return (None, repr(params))
  
  @classmethod
  def unserialize(cls, file, length=-1, charset=None):
    # return (list args, dict params)
    st = eval(file.read(length), {}, {})
    if isinstance(st, dict):
      return (None, st)
    elif isinstance(st, list):
      return (st, None)
    else:
      return ((st,), None)
  

serializers.register(PythonPySerializer)

if __name__ == '__main__':
  from datetime import datetime
  print PythonPySerializer.encode({
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
          'today': datetime.now()
        }
      }
    ],
    'today': datetime.now()
  })
