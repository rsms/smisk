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


class posts(root):
  def __call__(self, named_arg=None, *args, **kwargs):
    session.begin()
    post = Post(title='the title', body='das bothy')
    session.commit()
    # dir(Post) ['__class__', '__delattr__', '__dict__', '__doc__', '__getattribute__', '__hash__', '__init__', '__metaclass__', '__module__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__str__', '__weakref__', '_caller', '_class_state', '_descriptor', '_global_session', '_setup_done', 'body', 'c', 'count', 'count_by', 'delete', 'expire', 'expunge', 'filter', 'filter_by', 'flush', 'get', 'get_by', 'id', 'instances', 'join_to', 'join_via', 'mapper', 'merge', 'options', 'query', 'refresh', 'save', 'save_or_update', 'select', 'select_by', 'selectfirst', 'selectfirst_by', 'selectone', 'selectone_by', 'set', 'table', 'title', 'update']
    # dir(session) ['__call__', '__class__', '__contains__', '__delattr__', '__dict__', '__doc__', '__getattribute__', '__hash__', '__init__', '__iter__', '__module__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__str__', '__weakref__', 'begin', 'begin_nested', 'bind', 'clear', 'close', 'close_all', 'commit', 'configure', 'connection', 'delete', 'deleted', 'dirty', 'execute', 'expire', 'expunge', 'extension', 'flush', 'get', 'get_bind', 'identity_key', 'identity_map', 'is_modified', 'load', 'mapper', 'merge', 'new', 'object_session', 'query', 'query_property', 'refresh', 'registry', 'remove', 'rollback', 'save', 'save_or_update', 'scalar', 'session_factory', 'update']
    response.headers.append('Content-Type: text/xml')
    return [
      "newly created post = %s\n" % post,
      "Post.query.all() = %s\n" % repr(Post.query.all()),
      "from root > %s.__call__()\n" % repr(self),
      "  named_arg = %s\n" % repr(named_arg),
      "  args      = %s\n" % repr(args),
      "  kwargs    = %s\n" % repr(kwargs)
    ]
  
  def show(self, post_id=0, *args, **kwargs):
    response("from root > %s.show(post_id=%s)\n" % (repr(self), str(post_id)))
  
  class edit(root):
    def __call__(self, *args, **kwargs):
      response("from root > posts.%s.__call__()\n" % repr(self))
    
    def save(self, *args, **kwargs):
      response("from root > posts.%s.save()\n" % repr(self))
    
  
