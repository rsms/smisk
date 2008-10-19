# encoding: utf-8
'''
XML Property List serialization
'''
import re, logging
from smisk.codec import codecs, BaseCodec
from smisk.core.xml import escape as xml_escape
from datetime import datetime

log = logging.getLogger(__name__)

DOCTYPE = u'<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">'

class EncodeError(Exception):
  '''Indicates an encoding error'''
  pass

def start_rsp(charset):
  return [u'<?xml version="1.0" encoding="%s" ?>' % charset, DOCTYPE, u'<plist version="1.0">']

def finalize_rsp(v, glue=u"\n"):
  v.append(u'</plist>')
  return glue.join(v)

def encode_value(v, buf, level):
  indent = '  '*level
  if isinstance(v, bool):
    s = 'false'
    if v:
      s = 'true'
    buf.append('%s<%s/>' % (indent, s))
  elif isinstance(v, int):
    buf.append('%s<integer>%d</integer>' % (indent, v))
  elif isinstance(v, float):
    buf.append('%s<real>%f</real>' % (indent, v))
  elif isinstance(v, basestring):
    if len(v) > 256 and v.find('<![CDATA[') == -1:
      buf.append('%s<string><![CDATA[%s]]></string>' % (indent, v))
    else:
      buf.append('%s<string>%s</string>' % (indent, xml_escape(v)))
  elif isinstance(v, list) or isinstance(v, tuple):
    encode_sequence(v, buf, level)
  elif isinstance(v, dict):
    encode_map(v, buf, level)
  elif isinstance(v, datetime):
    buf.append('%s<date>%s</date>' % (indent, v.strftime('%Y-%m-%dT%H:%M:%SZ')))
  else:
    raise EncodeError(u'Unserializeable type %s' % type(v))

def encode_map(d, buf, level=1):
  indent = '  '*level
  buf.append('%s<dict>' % indent)
  items = d.items()
  items.sort()
  for k,v in items:
    buf.append('  %s<key>%s</key>' % (indent, xml_escape(k)))
    encode_value(v, buf, level+1)
  buf.append('%s</dict>' % indent)

def encode_sequence(l, buf, level):
  indent = '  '*level
  buf.append('%s<array>' % indent)
  for v in l:
    encode_value(v, buf, level+1)
  buf.append('%s</array>' % indent)


class codec(BaseCodec):
  '''XML Property List codec'''
  
  name = 'XML Property List'
  extensions = ('plist',)
  media_types = ('application/plist+xml',)
  charset = 'utf-8'
  
  @classmethod
  def encode(cls, params, charset):
    v = start_rsp(charset)
    encode_map(params, v)
    return (charset, finalize_rsp(v).encode(charset))
  
  #xxx todo implement decoder

codecs.register(codec)

if __name__ == '__main__':
  print codec.encode({
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
  })
