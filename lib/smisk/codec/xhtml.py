# encoding: utf-8
'''XHTML generic serialization
'''
from smisk.codec import codecs, BaseCodec
from smisk.mvc import http
from smisk.core.xml import escape as xml_escape
from smisk.core import Application

def encode_value(v, buf, value_wraptag='tt'):
  if isinstance(v, bool):
    if v:
      buf.append(u'<%s>True</%s>' % (value_wraptag, value_wraptag))
    else:
      buf.append(u'<%s>False</%s>' % (value_wraptag, value_wraptag))
  elif isinstance(v, list) or isinstance(v, tuple):
    encode_sequence(v, buf, value_wraptag)
  elif isinstance(v, dict):
    encode_map(v, buf, value_wraptag)
  else:
    buf.append(u'<%s>%s</%s>' % (value_wraptag, xml_escape(unicode(v)), value_wraptag) )
  return buf

def encode_map(d, buf, value_wraptag='tt'):
  buf.append(u'<ul>')
  items = d.items()
  items.sort()
  for k,v in items:
    buf.append(u'<li>%s: ' % xml_escape(unicode(k)) )
    encode_value(v, buf, value_wraptag)
    buf.append(u'</li>')
  buf.append(u'</ul>')
  return buf

def encode_sequence(l, buf, value_wraptag='tt'):
  buf.append(u'<ol>')
  for v in l:
    buf.append(u'<li>')
    encode_value(v, buf, value_wraptag)
    buf.append(u'</li>')
  buf.append(u'</ol>')
  return buf


class XHTMLCodec(BaseCodec):
  '''XHTML codec'''
  name = 'XHTML: Extensible Hypertext Markup Language'
  extensions = ('html',)
  media_types = ('text/html', 'application/xhtml+xml')
  charset = 'utf-8'
  
  @classmethod
  def encode(cls, params, charset):
    title = u'Response'
    server = u''
    if Application.current is not None and Application.current.destination is not None:
      title = u'/%s.html' % u'/'.join(Application.current.destination.path)
      server = Application.current.request.env['SERVER_SOFTWARE']
    d = [u'<?xml version="1.0" encoding="%s" ?>' % charset]
    d.append(u'<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" '\
             u'"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">')
    d.append(u'<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">')
    d.append(u'<head><title>%s</title>'\
      u'<style type="text/css">'\
        u'body{font-family:sans-serif;}'\
        u'ul,ol{margin-bottom:1em}'\
        u'</style>'\
      u'</head>' % xml_escape(title))
    d.append(u'<body>')
    d.append(u'<h1>%s</h1>' % xml_escape(title))
    encode_map(params, d)
    if server:
      d.append(u'<hr/><address>%s</address>' % server)
    d.append(u'</body></html>')
    return (charset, u''.join(d).encode(charset))
  
  @classmethod
  def encode_error(cls, status, params, charset):
    xp = {'charset':charset}
    for k,v in params.iteritems():
      if k == 'traceback':
        if v:
          v = u'<pre class="traceback">%s</pre>' % xml_escape(''.join(v))
        else:
          v = u''
      elif k == 'description':
        v = u''.join(encode_value(v, [], 'p'))
      else:
        v = xml_escape(unicode(v))
      xp[k] = v
    # Override if description_html is set
    if 'description_html' in params:
      xp['description'] = params['description_html']
    s = ERROR_TEMPLATE % xp
    return (charset, s.encode(charset))
  

codecs.register(XHTMLCodec)

ERROR_TEMPLATE = ur'''<?xml version="1.0" encoding="%(charset)s" ?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
  <head>
    <title>%(name)s</title>
    <style type="text/css">
      body,html { padding:0; margin:0; background:#666; }
      h1 { padding:25pt 10pt 10pt 15pt; background:#ffb2bf; color:#560c00; font-family:arial,helvetica,sans-serif; margin:0; }
      address, p { font-family:'lucida grande',verdana,arial,sans-serif; }
      body > p, body > ul, body > ol { padding:10pt 16pt; background:#fff; color:#222; margin:0; font-size:.9em; }
      pre.traceback { padding:10pt 15pt 25pt 15pt; line-height:1.4; background:#f2f2ca; color:#52523b; margin:0; border-top:1px solid #e3e3ba; border-bottom:1px solid #555; }
      hr { display:none; }
      address { padding:10pt 15pt; color:#333; font-size:11px; }
    </style>
  </head>
  <body>
    <h1>%(name)s</h1>
    %(description)s
    %(traceback)s
    <hr/>
    <address>%(server)s</address>
  </body>
</html>
'''

if __name__ == '__main__':
  from datetime import datetime
  s = XHTMLCodec.encode({
    'message': 'Hello worlds',
    'internets': [
      'interesting',
      'lolz',
      42.0,
      {
        'tubes': [1,3,16,18,24],
        'persons': True,
        'me again': {
          'message': 'Hello worlds',
          'internets': [
            'interesting',
            'lolz',
            42.0,
            {
              'tubes': [1,3,16,18,24],
              'persons': True
            }
          ],
          'today': datetime.now()
        }
      }
    ],
    'today': datetime.now()
  }, XHTMLCodec.charset)
  print s
