# encoding: utf-8
'''Types
'''
import sys, re
from types import *

if sys.version_info[0:2] <= (2, 5):
  try:
    from UserDict import DictMixin
  except ImportError:
    # DictMixin is new in Python 2.3
    class DictMixin: pass
  MutableMapping = DictMixin
else:
  from smisk import _MutableMapping as MutableMapping


class Symbol:
  '''General purpose named object.
  '''
  def __init__(self,name):
    self.name = name
  
  def __repr__(self):
    return self.name
  

Undefined = Symbol('Undefined')
'''Indicates an undefined value.
'''

None2 = (None, None)
''':type: tuple
'''

RegexType = type(re.compile('.'))
''':type: type
'''
