# encoding: utf-8
import sys, types

def expose(slug=None, template=None, formats=None):
  def entangle(func):
    if slug is not None and isinstance(slug, basestring):
      func.slug = str(slug)
    
    if template is not None:
      func.template = str(template)
    
    if formats is not None:
      if isinstance(formats, list):
        func.formats = formats
      else:
        func.formats = list(formats)
    
    return func
  
  if isinstance(slug, (types.FunctionType, types.MethodType)):
    return entangle(slug)
  return entangle


def hide(func=None):
  def entangle(func):
    func.hidden = True
    return func
  
  if isinstance(func, (types.FunctionType, types.MethodType)):
    return entangle(func)
  return entangle

