# encoding: utf-8
from smisk.mvc.control import *

print __file__

class ResourcesController(Application):
  def index(self, **args):
    return dict(resources=Resource.query.all())
  
