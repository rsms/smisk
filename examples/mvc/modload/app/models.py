# encoding: utf-8
from smisk.mvc.model import *

class Resource(Entity):
  url = Field(Unicode())
  hist = Field(Integer)
