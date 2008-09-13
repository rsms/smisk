# encoding: utf-8
from smisk.mvc.model import *

# Database
metadata.bind = 'sqlite:///'
#metadata.bind.echo = True

class Post(Entity):
  title = Field(Unicode())
  body = Field(Unicode())
