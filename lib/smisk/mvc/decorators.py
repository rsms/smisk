# encoding: utf-8
'''Controller tree function decorators.
'''
import types

__all__ = ['expose', 'hide']

def expose(slug=None, template=None, formats=None, delegates=False):
  '''Explicitly expose a function, optionally configure how it is exposed.
  '''
  def entangle(func):
    if slug is not None:
      # Slug might be the function if decorator called without ()
      if isinstance(slug, basestring):
        func.slug = unicode(slug)
      elif isinstance(slug, unicode):
        func.slug = slug
    
    if delegates is not None:
      func.delegates = bool(delegates)
    
    if template is not None:
      func.template = unicode(template)
    
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

