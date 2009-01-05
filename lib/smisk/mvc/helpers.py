# encoding: utf-8
'''Helpers
'''
from smisk.core import URL
from smisk.mvc import control, http
from smisk.mvc.model import Entity
import urllib

__all__ = ['compose_query', 'redirect_to']


def compose_query(params):
  '''Convert a mapping object to a URL encoded query string.
  The opposite can be found in smisk.core.URL.decompose_query().
  '''
  return urllib.urlencode(params, doseq=1)


def redirect_to(url, entity=None, status=http.Found, **params):
  '''Redirect the requesting client to someplace else.
  '''
  # If one or more entities are defined, add primary keys to params
  if entity is not None:
    if not isinstance(entity, (list, tuple)):
      entity = [entity]
    for ent in entity:
      for pk in ent.table.primary_key.keys():
        params[pk] = getattr(ent, pk)
  
  # The url might be a URL or leaf
  if not isinstance(url, basestring):
    if isinstance(url, URL):
      url = str(url)
    else:
      # url is probably an leaf
      url = control.uri_for(url)
  
  # Append any params to url
  if params:
    if not url.endswith('?'):
      if '?' in url:
        url += '&'
      else:
        url += '?'
    url += compose_query(params)
  
  # Status3xx.service() will perform further work on this url or 
  # path (absolutize it, etc)
  raise status(url)
