# encoding: utf-8
'''
Plain text encoding
'''
from smisk.serialization import serializers, Serializer

def encode_value(v, buf, level):
  if isinstance(v, bool):
    if v:
      buf.append(u'true')
    else:
      buf.append(u'false')
  elif isinstance(v, int):
    buf.append(u'%d' % v)
  elif isinstance(v, float):
    buf.append(u'%f' % v)
  elif isinstance(v, basestring):
    buf.append(unicode(v))
  elif isinstance(v, list) or isinstance(v, tuple):
    encode_sequence(v, buf, level)
  elif isinstance(v, dict):
    encode_map(v, buf, level)
  else:
    buf.append(unicode(v))
  return buf

def encode_map(d, buf, level=0):
  indent = u'  '*level
  #buf.append(u'\n')
  ln = len(d)
  i = 1
  items = d.items()
  items.sort()
  for k,v in items:
    buf.append(u'\n')
    buf.append(u'%s' % indent)
    buf.append(u'%s: ' % k)
    encode_value(v, buf, level+1)
    i += 1
  return buf

def encode_sequence(l, buf, level):
  indent = u'  '*level
  #buf.append(u'\n')
  ln = len(l)
  i = 1
  for v in l:
    buf.append(u'\n%s' % indent)
    encode_value(v, buf, level+1)
    i += 1
  return buf

class PlainTextSerializer(Serializer):
  '''Plain Text serializer.'''
  name = 'Plain text'
  extensions = ('txt',)
  media_types = ('text/plain',)
  charset = 'utf-8'
  
  @classmethod
  def serialize(cls, params, charset):
    s = u'%s\n' % u''.join(encode_map(params, [])).strip()
    return (charset, s.encode(charset, cls.unicode_errors))
  

serializers.register(PlainTextSerializer)

if __name__ == '__main__':
  from datetime import datetime
  print PlainTextSerializer.serialize({
    u'message': 'Hello worlds',
    'internets': [
      'interesting',
      'lolz',
      {
        'tubes': [1,3,16,18,24],
        'persons': True
      },
      42.0,
      {
        u'tubes': [1,3,16,18,24],
        u'persons': True,
        u'me again': {
          'message': 'Hello worlds',
          'internets': [
            u'interesting',
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
  }, PlainTextSerializer.charset)[1]
