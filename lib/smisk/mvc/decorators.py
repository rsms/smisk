# encoding: utf-8
import sys

def expose(slug=None, template=None, formats=None):
  #print >> sys.stderr, 'expose %r' % url_slug
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
  
  if slug is not None and not isinstance(slug, basestring):
    return entangle(slug)
  return entangle

def hide(x=None):
  #print >> sys.stderr, 'hide %r' % a
  def entangle(func):
    func.hidden = True
    return func
  
  if x is not None:
    return entangle(x)
  return entangle

