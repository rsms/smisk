# encoding: utf-8
import time, os, logging
from datetime import datetime
from smisk.mvc.control import Controller
from smisk.mvc.decorators import *
from smisk.mvc.exceptions import *

log = logging.getLogger(__name__)
print __file__

class Application(Controller):
  title = 'Hunch ar fett <yay> & mos!'
  time_since_last_req = 0
  last_req_time = time.time()
  fruits=['mango','ananas','lemon<b>mums</b> & smask!']
  
  def index(self, **args):
    t = time.time()
    self.time_since_last_req = int(t-self.last_req_time)
    self.last_req_time = t
    return args
  

class FilesController(Application):
  @expose(template=False)
  def send(self, **args):
    relpath = request.url.path.replace('..', '').lstrip('/')
    path = os.path.abspath(relpath)
    if not os.path.isfile(path):
      raise NotFound('No such file %r' % relpath)
    log.info("Sending file %r", path)
    response.send_file(path)
  

class Post(object):
  def __init__(self, title, body):
    self.title = title
    self.body = body
    self.date_published = datetime.now()
  

class PostsController(Application):
  def index(self, **args):
    log.info("args=%r", args)
    pass
  
  def show(self, theid=None, **args):
    #response.headers.append('Content-Type: text/plain')
    return dict(post=Post('Super Ninja', 'One upon a time, there was a little ninja sneaking around...'))
  
