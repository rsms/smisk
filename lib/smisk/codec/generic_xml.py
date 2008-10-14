# encoding: utf-8
'''
XML serialization
'''
import re, logging
from smisk.codec import codecs, BaseCodec
from smisk.core.xml import escape as xml_escape

log = logging.getLogger(__name__)

class EncodeError(Exception):
  '''Indicates an encoding error'''
  pass


def start_rsp(charset):
  return [u'<?xml version="1.0" encoding="%s" ?>' % charset, u'<rsp>']

def finalize_rsp(v, glue=u"\n"):
  v.append(u'</rsp>')
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


class codec(BaseCodec):
  '''XML codec'''
  
  extensions = ('xml',)
  media_types = ('text/xml',)
  charset = 'utf-8'
  
  @classmethod
  def encode(cls, params, charset):
    v = start_rsp(charset)
    encode_map(params, v)
    return (charset, finalize_rsp(v).encode(charset))
  
  @classmethod
  def encode_error(cls, status, params, charset):
    v = start_rsp(charset)
    msg = ' '.join([params['name'], params['description']])
    ends = ' />'
    if len(params) > 3:
      ends = '>'
    v.append('<err code="%d" msg="%s"%s' % \
      (int(params['code']), xml_escape(msg), ends))
    if ends == '>':
      del params['code']
      del params['name']
      del params['description']
      encode_map(params, v)
      v.append('</err>')
    return (charset, finalize_rsp(v).encode(charset))
  
  #xxx todo implement decoder

codecs.register(codec)
