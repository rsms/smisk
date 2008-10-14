# encoding: utf-8
'''
Plain text serialization
'''
from smisk.codec import codecs, BaseCodec
import re

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

class codec(BaseCodec):
  '''Plain Text codec.'''
  extensions = ('txt',)
  media_types = ('text/plain',)
  charset = 'utf-8'
  
  @classmethod
  def encode(cls, params, charset):
    s = u'{%s}\n' % ''.join(encode_map(params, [])).rstrip('\n')
    return (charset, s.encode(charset))
  

codecs.register(codec)

if __name__ == '__main__':
  from datetime import datetime
  print codec.encode({
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
