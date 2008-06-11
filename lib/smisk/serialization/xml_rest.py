# encoding: utf-8
'''
XML REST serialization
'''
import re, logging
from . import serializers, BaseSerializer
from smisk.core.xml import encode as xml_encode
from xmlrpclib import dumps, loads, Fault

log = logging.getLogger(__name__)
NODENAME_RE = re.compile(r'^[a-zA-Z0-9_-]+$')

class EncodeError(Exception):
  """Indicates an encoding error"""
  pass


def start_rsp():
  if Serializer.output_encoding is not None:
    return ['<?xml version="1.0" encoding="%s" ?>' % Serializer.output_encoding, '<rsp>']
  else:
    return ['<?xml version="1.0"?>', '<rsp>']

def finalize_rsp(v, glue="\n"):
  v.append('</rsp>')
  return glue.join(v)

def qualifies_as_nodename(s):
  if NODENAME_RE.match(s):
    return True
  return False

def encode_value(v, buf, level):
  indent = '  '*level
  if isinstance(v, int):
    buf.append('%s<int>%d</int>' % (indent, v))
  elif isinstance(v, float):
    buf.append('%s<real>%f</real>' % (indent, v))
  elif isinstance(v, basestring):
    if len(v) > 256 and v.find('<![CDATA[') == -1:
      buf.append('%s<string><![CDATA[%s]]></string>' % (indent, v))
    else:
      buf.append('%s<string>%s</string>' % (indent, xml_encode(v)))
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

def encode_map(d, buf, level):
  indent = '  '*level
  for k,v in d.iteritems():
    buf.append('%s<param name="%s">' % (indent, xml_encode(k)))
    encode_value(v, buf, level+1)
    buf.append('%s</param>' % indent)

def encode_sequence(l, buf, level):
  for v in l:
    encode_value(v, buf, level)


class Serializer(BaseSerializer):
  '''XML REST serializer'''
  
  output_type = 'application/rest+xml'
  output_encoding = 'utf-8'
  
  @classmethod
  def encode(cls, *args, **params):
    v = start_rsp()
    if len(args) and len(params):
      encode_sequence((args, params), v, 1)
    elif len(args):
      encode_sequence(args, v, 1)
    else:
      encode_map(params, v, 1)
    return finalize_rsp(v)
  
  @classmethod
  def encode_error(cls, typ, val, tb):
    v = start_rsp()
    v.append('<err code="%d" msg="%s" />' % (int(getattr(val, 'http_code', 0)), xml_encode(str(val))))
    return finalize_rsp(v)
  
  #xxx todo implement decoder

serializers[Serializer.output_type] = Serializer
