# encoding: utf-8
'''String parsing, formatting, etc.
'''
import sys, os
from smisk.core import URL, Application

__all__ = ['parse_qvalue_header', 'tokenize_path', 'strip_filename_extension', 'normalize_url']

def parse_qvalue_header(s, accept_any_equals='*/*', partial_endswith='/*', return_true_if_accepts_charset=None):
  '''Parse a qvalue HTTP header'''
  vqs = []
  highqs = []
  partials = []
  accept_any = False
  
  if not partial_endswith:
    partial_endswith = None
  
  for part in s.split(','):
    part = part.strip(' ')
    p = part.find(';')
    if p != -1:
      # todo Find out what the undocumented, but revealed, level= tags in HTTP 1.1 
      #      really mean and if they exists in reality. As they are not documented,
      #      we will not implement support for it. [RFC 2616, chapter 14.1 "Accept"]
      pp = part.find('q=', p)
      if pp != -1:
        q = int(float(part[pp+2:])*100.0)
        part = part[:p]
        if return_true_if_accepts_charset is not None and part == return_true_if_accepts_charset:
          return (True, True, True, True)
        vqs.append([part, q])
        if q == 100:
          highqs.append(part)
        continue
    # No qvalue; we use three classes: any (q=0), partial (q=50) and complete (q=100)
    if return_true_if_accepts_charset is not None and part == return_true_if_accepts_charset:
      return (True, True, True, True)
    qual = 100
    if part == accept_any_equals:
      qual = 0
      accept_any = True
    else:
      if partial_endswith is not None and part.endswith('/*'):
        partial = part[:-2]
        if not partial:
          continue
        qual = 50
        partials.append(partial) # remove last char '*'
      else:
        highqs.append(part)
    vqs.append([part, qual])
  # Order by qvalue
  vqs.sort(lambda a,b: b[1] - a[1])
  return vqs, highqs, partials, accept_any


def tokenize_path(path):
  '''Deconstruct a URI path into standardized tokens.
  
  :param path: A pathname
  :type  path: string
  :rtype: list'''
  tokens = []
  for tok in strip_filename_extension(path).split('/'):
    tok = URL.decode(tok)
    if len(tok):
      tokens.append(tok)
  return tokens

def strip_filename_extension(fn):
  '''Remove any file extension from filename.
  
  :rtype: string
  '''
  try:
    return fn[:fn.rindex('.')]
  except:
    return fn

def normalize_url(url, ref_base_url=None):
  '''
  :param url:
    An absolute URL, absolute path or relative path.
  :type  url:
    URL | string
  :param ref_base_url:
    Default absolute URL used to expand a path to a full URL.
    Uses ``smisk.core.request.url`` if not set.
  :type  ref_base_url:
    URL
  :rtype:
    URL
  '''
  is_relative_uri = False
  if '/' not in url:
    is_relative_uri = True
    u = URL()
    u.path = url
    url = u
  else:
    url = URL(url) # make a copy so we don't modify the original
  
  if not ref_base_url:
    if Application.current and Application.current.request:
      ref_base_url = Application.current.request.url
    else:
      ref_base_url = URL()
  
  if url.scheme is None:
    url.scheme = ref_base_url.scheme
  if url.user is None:
    url.user = ref_base_url.user
    if url.user is not None and url.password is None:
      url.password = ref_base_url.password
  if url.host is None:
    url.host = ref_base_url.host
  if url.port == 0:
    url.port = ref_base_url.port
  if is_relative_uri:
    base_path = ref_base_url.path
    if not base_path:
      base_path = '/'
    elif not base_path.endswith('/'):
      base_path = base_path + '/'
    url.path = base_path + url.path
  
  return url
