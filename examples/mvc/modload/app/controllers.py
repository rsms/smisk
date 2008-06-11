# encoding: utf-8
import sys, os, logging, time
from smisk.mvc.control import Controller

log = logging.getLogger(__name__)

class root(Controller):
  def __call__(self, *args, **kwargs):
    log.debug('root.__call__: got args: %s  kwargs: %s', repr(args), repr(kwargs))
    return dict(
      title = "This is a title",
      message = "This message was created at %f" % time.time(),
      aset = {
        "crazy<nyckel": "mos",
        "en annan nyckel": [123, 45.72401, "You", u"Uniyou", ("A", "B", r'C')]
      }
    )
  
  def posts(self, *args, **kwargs):
    pass


class posts(root):
  def __call__(self, named_arg=None, *args, **kwargs):
    response(
      "from root > %s.__call__()\n" % repr(self),
      "  named_arg = %s\n" % repr(named_arg),
      "  args      = %s\n" % repr(args),
      "  kwargs    = %s\n" % repr(kwargs)
    )
  
  def show(self, post_id=0, *args, **kwargs):
    response("from root > %s.show(post_id=%s)\n" % (repr(self), str(post_id)))
  
  class edit(root):
    def __call__(self, *args, **kwargs):
      response("from root > posts.%s.__call__()\n" % repr(self))
    
    def save(self, *args, **kwargs):
      response("from root > posts.%s.save()\n" % repr(self))
    
  
