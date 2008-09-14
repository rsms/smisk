# encoding: utf-8
import logging
from smisk.mvc.control import Controller
log = logging.getLogger(__name__)

class root(Controller):
  def __call__(self, *args, **kwargs):
    pass
  
