# encoding: utf-8
from ..util import Singleton
from ..inflection import inflection
from smisk.mvc.decorators import *
from smisk.mvc.exceptions import *

class Controller(Singleton):
  @classmethod
  def controller_name(cls):
    return inflection.underscore(cls.__name__.replace('Controller',''))
  
