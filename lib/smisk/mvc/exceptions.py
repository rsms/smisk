# encoding: utf-8
class MVCError(Exception):
  pass

class NotFound(MVCError):
  http_code = 404

class ControllerNotFound(NotFound):
  pass

class ActionNotFound(NotFound):
  pass

class TemplateNotFound(NotFound):
  pass

