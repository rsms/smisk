# encoding: utf-8
'''Example of a very simple "bare bones" text serializer
'''
from smisk.serialization import Serializer, serializers

class MyTextSerializer(Serializer):
  '''My simple text format
  '''
  # See the code in my_xml_serializer.py for explanation of the following
  # attributes:
  name = 'My text'
  extensions = ('mytext',)
  media_types = ('text/x-mytext',)
  charset = 'utf-8'
  can_serialize = True
  
  @classmethod
  def serialize(cls, params, charset):
    s = u'This is the response:\n'
    for kv in params.items():
      s += u'  %s: %s\n' % kv
    # This method must return a tuple of ( str<charset actually used>, str<data> )
    return (charset, s.encode(charset))
  

serializers.register(MyTextSerializer)
