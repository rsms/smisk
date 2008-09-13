# encoding: utf-8
class MVCError(Exception):
  pass

class NotFound(MVCError):
  http_code = 404
  
  def __call__(self, *args, **kwargs):
    raise self
  

class ControllerNotFound(NotFound):
  pass

class MethodNotFound(NotFound):
  pass

class TemplateNotFound(NotFound):
  pass

