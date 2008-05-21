# encoding: utf-8
from ..util import Singleton
from ..inflection import inflection
from smisk.mvc.decorators import *
from smisk.mvc.exceptions import *
from smisk.core import Application as App

class Controller(object):
  def __new__(type):
    if not '_instance' in type.__dict__:
      type._instance = object.__new__(type)
    return type._instance
  
  @classmethod
  def controller_name(cls):
    return inflection.underscore(cls.__name__.replace('Controller',''))
  
