# encoding: utf-8
'''String parsing, formatting, etc.
'''
import sys, os
from smisk.core import URL, request

__all__ = ['parse_qvalue_header', 'tokenize_path', 'strip_filename_extension', 'normalize_url']

def parse_qvalue_header(s, accept_any_equals='*/*', partial_endswith='/*'):
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
        vqs.append([part, q])
        if q == 100:
          highqs.append(part)
        continue
    # No qvalue; we use three classes: any (q=0), partial (q=50) and complete (q=100)
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

def normalize_url(url, default_absolute_url=None):
  '''
  :Parameters:
    url : string
      An absolute URL, absolute path or relative path
    default_absolute_url : URL
      Default absolute URL used to expand a path to a full URL.
      Uses ``smisk.core.request.url`` if not set.
  :rtype: string
  '''
  if url.find('://') == -1:
    # url is actually a path
    path = url
    if default_absolute_url:
      url = default_absolute_url
    elif request:
      url = request.url
    else:
      url = URL()
    if len(path) == 0:
      path = '/'
    elif path[0] != '/':
      if url.path:
        path = os.path.normpath(url.path) + '/' + os.path.normpath(path)
      else:
        path = '/' + os.path.normpath(path)
    else:
      path = os.path.normpath(path)
    url = url.to_s(port=url.port!=80, path=0, query=0, fragment=0) + path
  return url
