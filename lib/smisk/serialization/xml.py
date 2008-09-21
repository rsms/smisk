# encoding: utf-8
'''
XML serialization
'''
import re, logging
from smisk.serialization import serializers, BaseSerializer
from smisk.core.xml import escape as xml_escape

log = logging.getLogger(__name__)

class EncodeError(Exception):
  """Indicates an encoding error"""
  pass


def start_rsp():
  if Serializer.encoding is not None:
    return ['<?xml version="1.0" encoding="%s" ?>' % Serializer.encoding, '<rsp>']
  else:
    return ['<?xml version="1.0"?>', '<rsp>']

def finalize_rsp(v, glue="\n"):
  v.append('</rsp>')
  return glue.join(v)

def encode_value(v, buf, level):
  indent = '  '*level
  if isinstance(v, bool):
    s = 'false'
    if v:
      s = 'true'
    buf.append('%s<%s />' % (indent, s))
  elif isinstance(v, int):
    buf.append('%s<int>%d</int>' % (indent, v))
  elif isinstance(v, float):
    buf.append('%s<real>%f</real>' % (indent, v))
  elif isinstance(v, basestring):
    if len(v) > 256 and v.find('<![CDATA[') == -1:
      buf.append('%s<string><![CDATA[%s]]></string>' % (indent, v))
    else:
      buf.append('%s<string>%s</string>' % (indent, xml_escape(v)))
  elif isinstance(v, list) or isinstance(v, tuple):
    buf.append('%s<array>' % indent)
    encode_sequence(v, buf, level+1)
    buf.append('%s</array>' % indent)
  elif isinstance(v, dict):
    buf.append('%s<dict>' % indent)
    encode_map(v, buf, level+1)
    buf.append('%s</dict>' % indent)
  else:
    raise EncodeError('Unserializeable type %s' % str(type(v)))

def encode_map(d, buf, level=1):
  indent = '  '*level
  for k,v in d.iteritems():
    buf.append('%s<param name="%s">' % (indent, xml_escape(k)))
    encode_value(v, buf, level+1)
    buf.append('%s</param>' % indent)

def encode_sequence(l, buf, level):
  for v in l:
    encode_value(v, buf, level)


class Serializer(BaseSerializer):
  '''XML serializer'''
  
  extension = 'xml'
  media_type = 'text/xml'
  encoding = 'utf-8'
  
  @classmethod
  def encode(cls, **params):
    v = start_rsp()
    encode_map(params, v)
    return finalize_rsp(v)
  
  @classmethod
  def encode_error(cls, status, params, typ, val, tb):
    v = start_rsp()
    if 'code' in params and 'message' in params:
      ends = ' />'
      if len(params) > 2:
        ends = '>'
      v.append('<err code="%d" msg="%s"%s' % \
        (int(params['code']), xml_escape(str(params['message'])), ends))
      if ends == '>':
        del params['code']
        del params['message']
        encode_map(params, v)
        v.append('</err>')
    else:
      encode_map(params, v)
    return finalize_rsp(v)
  
  #xxx todo implement decoder

serializers.register(Serializer)
