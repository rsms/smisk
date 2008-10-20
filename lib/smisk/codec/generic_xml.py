# encoding: utf-8
'''
XML serialization
'''
import re, logging
from smisk.codec import codecs, BaseCodec, EncodingError
from smisk.core.xml import escape as xml_escape

log = logging.getLogger(__name__)

def start_rsp(charset):
  return [u'<?xml version="1.0" encoding="%s" ?>' % charset, u'<rsp>']

def finalize_rsp(v, glue=u"\n"):
  v.append(u'</rsp>')
  return glue.join(v)

def encode_value(v, buf, level):
  indent = u'  '*level
  if isinstance(v, bool):
    s = u'false'
    if v:
      s = u'true'
    buf.append(u'%s<%s />' % (indent, s))
  elif isinstance(v, int):
    buf.append(u'%s<int>%d</int>' % (indent, v))
  elif isinstance(v, float):
    buf.append(u'%s<real>%f</real>' % (indent, v))
  elif isinstance(v, basestring):
    if isinstance(v, str):
      v = unicode(v)
    if len(v) > 256 and v.find(u'<![CDATA[') == -1:
      buf.append(u'%s<string><![CDATA[%s]]></string>' % (indent, v))
    else:
      buf.append(u'%s<string>%s</string>' % (indent, xml_escape(v)))
  elif isinstance(v, list) or isinstance(v, tuple):
    buf.append(u'%s<array>' % indent)
    encode_sequence(v, buf, level+1)
    buf.append(u'%s</array>' % indent)
  elif isinstance(v, dict):
    buf.append(u'%s<dict>' % indent)
    encode_map(v, buf, level+1)
    buf.append(u'%s</dict>' % indent)
  else:
    raise EncodingError(u'Unserializeable type %s' % type(v))

def encode_map(d, buf, level=1):
  indent = '  '*level
  items = d.items()
  items.sort()
  for k,v in items:
    buf.append(u'%s<param name="%s">' % (indent, xml_escape(k)))
    encode_value(v, buf, level+1)
    buf.append(u'%s</param>' % indent)

def encode_sequence(l, buf, level):
  for v in l:
    encode_value(v, buf, level)


class codec(BaseCodec):
  '''XML codec'''
  name = 'Generic XML'
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
    msg = u' '.join([params['name'], params['description']])
    ends = u' />'
    if len(params) > 3:
      ends = u'>'
    v.append(u'<err code="%d" msg="%s"%s' % \
      (int(params['code']), xml_escape(msg), ends))
    if ends == u'>':
      del params['code']
      del params['name']
      del params['description']
      encode_map(params, v)
      v.append(u'</err>')
    return (charset, finalize_rsp(v).encode(charset))
  
  #xxx todo implement decoder

codecs.register(codec)
