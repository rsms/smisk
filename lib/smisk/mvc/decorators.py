# encoding: utf-8
'''Controller tree function decorators.
'''
import types
import smisk.mvc.filters

__all__ = ['expose', 'hide']

def expose(slug=None, template=None, formats=None, delegates=False, filters=None, methods=None):
  '''Explicitly expose a function, optionally configure how it is exposed.
  '''
  def entangle(func):
    # Note: We do not add default values (i.e. methods = None) because we can not gurantee
    #       that every leaf called has been @expose'd, so we need to check for attribute
    #       existance anyway outside of this scope.
    
    # Slug
    if slug is not None:
      # Slug might be the function if decorator called without ()
      if isinstance(slug, basestring):
        func.slug = unicode(slug)
      elif isinstance(slug, unicode):
        func.slug = slug
    
    # Delegates to other leafs up the class hierarchy?
    if delegates is not None:
      func.delegates = bool(delegates)
    
    # Template
    if template is not None:
      func.template = unicode(template)
    
    # Formats
    if formats is not None:
      if isinstance(formats, (list, tuple)):
        func.formats = formats
      else:
        func.formats = (formats,)
      for s in func.formats:
        if not isinstance(s, basestring):
          raise TypeError('formats must be a tuple or list of strings, alternatively a single string')
    
    # Filters
    if filters is not None:
      if isinstance(filters, list):
        func.filters = filters
      else:
        func.filters = [filters]
      for f in func.filters:
        if not hasattr(f, 'before') or not callable(f.before) or not hasattr(f, 'after') or not callable(f.after):
          raise TypeError('filter %r must have two callable attributes: before and after' % f)
    
    # Methods
    if methods is not None:
      if isinstance(methods, (list, tuple)):
        func.methods = methods
      else:
        func.methods = (methods,)
      for s in func.methods:
        if not isinstance(s, basestring):
          raise TypeError('methods must be a tuple or list of strings, alternatively a single string')
      func.methods = [s.upper() for s in func.methods]
    
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

