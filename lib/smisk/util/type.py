# encoding: utf-8
'''Types
'''
import re
from types import *

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
