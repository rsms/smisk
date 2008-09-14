# encoding: utf-8
import sys, os, logging, time
from smisk.mvc.control import Controller
from models import *

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
    # this will never be called from the outside, as class posts shadows this.


class posts(root):
  def __call__(self, *args, **kwargs):
    session.begin()
    post = Post(title='the title', body='das bothy')
    session.commit()
    return {
      "post": post,
      "Post.query.all()": repr(Post.query.all()),
      "Method called": "%s.__call__()\n" % repr(self),
      "Request args": repr(args),
      "Request params": repr(kwargs)
    }
  
  def show(self, post_id=0, *args, **kwargs):
    return {'message': "from root > %s.show(post_id=%s)" % (repr(self), str(post_id))}
  
  class edit(root):
    def __call__(self, *args, **kwargs):
      return {'message': "from root > posts.%s.__call__()" % repr(self)}
    
    def save(self, *args, **kwargs):
      return {'message': "from root > posts.%s.save()" % repr(self)}
    
  
