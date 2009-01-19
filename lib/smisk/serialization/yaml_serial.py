# encoding: utf-8
'''
YAML: Human-readable data serialization

:see: `YAML 1.1 <http://yaml.org/spec/1.1/>`__
:requires: `PyYAML <http://pyyaml.org/wiki/PyYAML>`__
'''
import sys, logging
log = logging.getLogger(__name__)
from smisk.serialization import serializers, Serializer, data as opaque_data
__all__ = ['YAMLSerializer', 'yaml']
try:
  import yaml
  try:
    from yaml import CSafeLoader as Loader, CSafeDumper as Dumper
  except ImportError:
    from yaml import SafeLoader as Loader, SafeDumper as Dumper
  __all__.extend(['Loader', 'Dumper'])
except ImportError:
  yaml = None

class YAMLSerializer(Serializer):
  '''Human-readable data serialization
  '''
  name = 'YAML'
  extensions = ('yaml',)
  media_types = ('application/x-yaml', 'text/yaml', 'text/x-yaml')
  charset = 'utf-8'
  supported_charsets = ('utf-8', 'utf-16-be', 'utf-16-le', None) # None == unicode
  
  @classmethod
  def serialize(cls, params, charset=None):
    if charset not in cls.supported_charsets:
      charset = cls.charset
    return (charset, yaml.dump(params, encoding=charset, Dumper=Dumper, allow_unicode=True))
  
  @classmethod
  def unserialize(cls, file, length=-1, charset=None):
    # return (collection args, dict params)
    s = file.read(length)
    if charset:
      s = s.decode(charset, cls.unicode_errors)
    st = yaml.load(s, Loader=Loader)
    if isinstance(st, dict):
      return (None, st)
    elif isinstance(st, list):
      return (st, None)
    else:
      return ((st,), None)
  

# Register if we have a backing YAML implementation
if yaml is not None:
  serializers.register(YAMLSerializer)
  
  # support for serializing Entities:
  from smisk.mvc.model import Entity
  def entity_serializer(dumper, entity):
    return dumper.represent_data(entity.to_dict())
  
  log.debug('registering smisk.mvc.model.Entity YAML serializer (W)')
  Dumper.add_multi_representer(Entity, entity_serializer)
  
  # support for serializing data:
  def data_serializer(dumper, dat):
    return dumper.represent_scalar(u'!data', dat.encode())
  
  def data_unserializer(loader, datatype, node):
    return opaque_data.decode(node.value)
  
  log.debug('registering smisk.serialization.data YAML serializer (RW)')
  Dumper.add_multi_representer(opaque_data, data_serializer)
  Loader.add_multi_constructor(u'!data', data_unserializer)


if __name__ == '__main__':
  data = {
    'message': 'Hello worlds',
    'internets': [
      'interesting',
      'lolz',
      42.0,
      {
        'abcdata': opaque_data('xyz detta överförs binärt'),
        'tubes': [1,3,16,18,24],
        'persons': True,
        u'me agåain': {
          'message': 'Hello worlds',
          'internets': [
            'interesting',
            'lolz',
            42.0,
            {
              'tubes': [1,3,16,18,24],
              'persons': True
            }
          ]
        }
      }
    ]
  }
  s = YAMLSerializer.serialize(data)[1]
  print s
  from StringIO import StringIO
  print repr(YAMLSerializer.unserialize(StringIO(s)))
