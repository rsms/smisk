#!/usr/bin/env python
# encoding: utf-8
from smisk.mvc import *
from smisk.serialization import data
import datetime, time

# Importing the serializers causes them to be registered
import my_xml_serializer
import my_text_serializer

# Some demo data
DEMO_STRUCT = dict(
  string = "Doodah",
  items = ["A", "B", 12, 32.1, [1, 2, 3]],
  float = 0.1,
  integer = 728,
  dict = dict(
    str = "<hello & hi there!>",
    unicode = u'M\xe4ssig, Ma\xdf',
    true_value = True,
    false_value = False,
  ),
  data = data("<binary gunk>"),
  more_data = data("<lots of binary gunk>" * 10),
  date = datetime.datetime.fromtimestamp(time.mktime(time.gmtime())),
)

# Our controller tree
class root(Controller):
  def __call__(self, *args, **params):
    '''Return some data
    '''
    return DEMO_STRUCT

  def echo(self, *va, **kw):
    '''Returns the structure received
    '''
    if not kw and va:
      kw['arguments'] = va
    return kw
  

if __name__ == '__main__':
  from smisk.config import config
  config.loads('"logging": {"levels":{"":DEBUG}}')
  main()
