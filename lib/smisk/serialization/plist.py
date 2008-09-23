# encoding: utf-8
'''
XML Property List serialization
'''
import re, logging
from smisk.serialization import serializers, BaseSerializer
from smisk.core.xml import escape as xml_escape
from datetime import datetime

log = logging.getLogger(__name__)

DOCTYPE = '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '\
          '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">'

class EncodeError(Exception):
  '''Indicates an encoding error'''
  pass

def start_rsp():
  if Serializer.encoding is not None:
    return ['<?xml version="1.0" encoding="%s" ?>' % Serializer.encoding, DOCTYPE, '<plist version="1.0">']
  else:
    return ['<?xml version="1.0"?>', DOCTYPE, '<plist version="1.0">']

def finalize_rsp(v, glue="\n"):
  v.append('</plist>')
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
    raise EncodeError('Unserializeable type %s' % str(type(v)))

def encode_map(d, buf, level=1):
  indent = '  '*level
  buf.append('%s<dict>' % indent)
  for k,v in d.iteritems():
    buf.append('  %s<key>%s</key>' % (indent, xml_escape(k)))
    encode_value(v, buf, level+1)
  buf.append('%s</dict>' % indent)

def encode_sequence(l, buf, level):
  indent = '  '*level
  buf.append('%s<array>' % indent)
  for v in l:
    encode_value(v, buf, level+1)
  buf.append('%s</array>' % indent)


class Serializer(BaseSerializer):
  '''XML Property list serializer'''
  
  extensions = ('plist',)
  media_types = ('application/plist+xml',)
  encoding = 'utf-8'
  
  @classmethod
  def encode(cls, **params):
    v = start_rsp()
    encode_map(params, v)
    return finalize_rsp(v)
  
  @classmethod
  def encode_error(cls, status, params, typ, val, tb):
    return cls.encode(**params)
  
  #xxx todo implement decoder

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
        'persons': True
      }
    ],
    'today': datetime.now()
  })
