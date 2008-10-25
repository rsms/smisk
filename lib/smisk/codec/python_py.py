# encoding: utf-8
'''
Plain text encoding
'''
from smisk.codec import codecs, BaseCodec

class PythonPyCodec(BaseCodec):
  '''Python code codec.'''
  name = 'Python code'
  extensions = ('py',)
  media_types = ('text/x-python',)
  
  @classmethod
  def encode(cls, params, charset):
    return (None, repr(params))
  
  @classmethod
  def decode(cls, file, length=-1, charset=None):
    # return (list args, dict params)
    st = eval(file.read(length), {}, {})
    if isinstance(st, dict):
      return (None, st)
    elif isinstance(st, list):
      return (st, None)
    else:
      return ((st,), None)
  

codecs.register(PythonPyCodec)

if __name__ == '__main__':
  from datetime import datetime
  print PythonPyCodec.encode({
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
