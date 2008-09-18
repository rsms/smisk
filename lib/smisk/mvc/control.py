# encoding: utf-8
from smisk.util import Singleton
from smisk.inflection import inflection
from smisk.mvc.decorators import *
from smisk.mvc.exceptions import *
from smisk.core import Application as App

class Controller(object):
  def __new__(type):
    if not '_instance' in type.__dict__:
      o = object.__new__(type)
      for k in dir(o):
        if k[0] != '_':
          o.__dict__[k] = getattr(o, k)
      type._instance = o
    return type._instance
  
  @classmethod
  def controller_name(cls):
    return inflection.underscore(cls.__name__.replace('Controller',''))
  
