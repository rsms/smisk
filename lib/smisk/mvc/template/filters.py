# encoding: utf-8
'''Template filters
'''

def j(s):
  """Escape for JavaScript or encode as JSON"""
  pass

try:
  from cjson import encode as _json
except ImportError:
  try:
    from minjson import write as _json
  except ImportError:
    import re
    _RE = re.compile(r'(["\'\\])')
    def _json(s):
      return repr(_RE.sub(r'\\\1', s)).replace('\\\\','\\')
j = _json
