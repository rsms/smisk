# encoding: utf-8
'''Plain text serialization.
'''
from smisk.serialization import serializers, Serializer
from smisk.serialization.yaml_serial import yaml, YAMLSerializer

if not yaml:
  def _encode_value(v, buf, level):
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
      _encode_sequence(v, buf, level)
    elif isinstance(v, dict):
      _encode_map(v, buf, level)
    else:
      buf.append(unicode(v))
    return buf

  def _encode_map(d, buf, level=0):
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
      _encode_value(v, buf, level+1)
      i += 1
    return buf

  def _encode_sequence(l, buf, level):
    indent = u'  '*level
    #buf.append(u'\n')
    ln = len(l)
    i = 1
    for v in l:
      buf.append(u'\n%s' % indent)
      _encode_value(v, buf, level+1)
      i += 1
    return buf


class PlainTextSerializer(Serializer):
  '''Human-readable plain text'''
  name = 'Plain text'
  extensions = ('txt',)
  media_types = ('text/plain',)
  charset = 'utf-8'
  can_serialize = True
  
  if yaml:
    # If we have YAML-capabilities we use YAML for plain text output
    @classmethod
    def serialize(cls, params, charset):
      return YAMLSerializer.serialize(params, charset)
  else:
    @classmethod
    def serialize(cls, params, charset):
      s = u'%s\n' % u''.join(_encode_map(params, [])).strip()
      return (charset, s.encode(charset, cls.unicode_errors))
    
  

serializers.register(PlainTextSerializer)
