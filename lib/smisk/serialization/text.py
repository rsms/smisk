# encoding: utf-8
'''
Plain text serialization
'''
from smisk.serialization import serializers, BaseSerializer
from datetime import datetime
import re

KEY_SAFE_RE = re.compile(r'^[a-zA-Z0-9_\.]+$')

def encode_value(v, buf, level):
  indent = '  '*level
  if isinstance(v, bool):
    if v:
      buf.append('true')
    else:
      buf.append('false')
  elif isinstance(v, int):
    buf.append('%d' % v)
  elif isinstance(v, float):
    buf.append('%f' % v)
  elif isinstance(v, basestring):
    buf.append('%r' % v)
  elif isinstance(v, list) or isinstance(v, tuple):
    encode_sequence(v, buf, level)
  elif isinstance(v, dict):
    encode_map(v, buf, level)
  else:
    buf.append('%r' % v)


def encode_map(d, buf, level=0):
  indent = '  '*level
  if level:
    buf.append('{\n')
  ln = len(d)
  i = 1
  for k,v in d.iteritems():
    if KEY_SAFE_RE.match(k):
      buf.append('%s%s: ' % (indent, k))
    else:
      buf.append('%s%r: ' % (indent, k))
    encode_value(v, buf, level+1)
    if i < ln:
      buf.append(',\n')
    else:
      buf.append('\n')
    i += 1
  if level > 0:
    buf.append('%s}' % ('  '*(level-1)))
  return buf

def encode_sequence(l, buf, level):
  indent = '  '*level
  buf.append('[\n')
  ln = len(l)
  i = 1
  for v in l:
    buf.append(indent)
    encode_value(v, buf, level+1)
    if i < ln:
      buf.append(',\n')
    else:
      buf.append('\n')
    i += 1
  buf.append('%s]' % ('  '*(level-1)))

class Serializer(BaseSerializer):
  '''Plain Text serializer.'''
  extensions = ('txt',)
  media_types = ('text/plain',)
  encoding = 'utf-8'
  
  @classmethod
  def encode(cls, **params):
    return ''.join(encode_map(params, []))
  
  @classmethod
  def encode_error(cls, status, params, typ, val, tb):
    if 'message' in params:
      msg = params['message']
    else:
      msg = cls.encode(**params)
    return '\n'.join([str(status), msg])+'\n'
  

serializers.register(Serializer)

if __name__ == '__main__':
  print Serializer.encode(**{
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
