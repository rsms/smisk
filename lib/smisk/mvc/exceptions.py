# encoding: utf-8
class MVCError(Exception):
  pass

class NotFound(MVCError):
  http_code = 404

class ControllerNotFound(NotFound):
  pass

class MethodNotFound(NotFound):
  pass

class TemplateNotFound(NotFound):
  pass

