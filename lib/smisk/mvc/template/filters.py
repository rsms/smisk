# encoding: utf-8
'''
Template filters
'''

try:
  from cjson import encode as j
except ImportError:
  try:
    from minjson import write as j
  except ImportError:
    import re
    J_RE = re.compile(r'(["\'\\])')
    def j(s):
      return repr(J_RE.sub(r'\\\1', s)).replace('\\\\','\\')
