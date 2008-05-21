# encoding: utf-8
import sys, os, logging, time
from smisk.mvc.control import Controller

log = logging.getLogger(__name__)

class root(Controller):
  def __call__(self, *args, **params):
    return dict(
      title = "This is a title",
      message = "This message was created at %f" % time.time()
    )
  
  def posts(self, *args, **params):
    pass


class posts(root):
  def __call__(self, *args, **params):
    response("from root > %s.__call__()\n" % repr(self))
  
  def show(self, post_id=0, *args, **params):
    response("from root > %s.show(post_id=%s)\n" % (repr(self), str(post_id)))
  
  class edit(root):
    def __call__(self, *args, **params):
      response("from root > posts.%s.__call__()\n" % repr(self))
    
    def save(self, *args, **params):
      response("from root > posts.%s.save()\n" % repr(self))
    
  
