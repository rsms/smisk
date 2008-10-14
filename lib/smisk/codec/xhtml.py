# encoding: utf-8
'''
JSON serialization (RFC 4627)
'''
from smisk.codec import codecs, BaseCodec
from smisk.mvc import http
from smisk.core.xml import escape as xml_escape
from smisk.core import Application

def encode_value(v, buf):
  if isinstance(v, bool):
    if v:
      buf.append(u'<em>True</em>')
    else:
      buf.append(u'<em>False</em>')
  elif isinstance(v, list) or isinstance(v, tuple):
    encode_sequence(v, buf)
  elif isinstance(v, dict):
    encode_map(v, buf)
  else:
    buf.append(u'<tt>%s</tt>' % xml_escape(repr(v)))

def encode_map(d, buf):
  buf.append(u'<ul>')
  for k,v in d.iteritems():
    buf.append(u'<li><b>%s:</b> ' % xml_escape(str(k)) )
    encode_value(v, buf)
    buf.append(u'</li>')
  buf.append(u'</ul>')

def encode_sequence(l, buf):
  buf.append(u'<ol>')
  for v in l:
    buf.append(u'<li>')
    encode_value(v, buf)
    buf.append(u'</li>')
  buf.append(u'</ol>')


class codec(BaseCodec):
  '''XHTML codec'''
  extensions = ('html',)
  media_types = ('text/html', 'application/xhtml+xml')
  charset = 'utf-8'
    
  @classmethod
  def encode(cls, params, charset):
    title = u'Response'
    if Application.current is not None and Application.current.destination is not None:
      title = u'/%s.html' % u'/'.join(Application.current.destination.path)
    d = [u'<?xml version="1.0" encoding="%s" ?>' % charset]
    d.append(u'<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" '\
             u'"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">')
    d.append(u'<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">')
    d.append(u'<head><title>%s</title></head>' % xml_escape(title))
    d.append(u'<body>')
    d.append(u'<h1>%s</h1><ol>' % xml_escape(title))
    encode_map(params, d)
    d.append(u'</ol>')
    d.append(u'</body>')
    d.append(u'</html>')
    return (charset, u''.join(d).encode(charset))
  
  @classmethod
  def encode_error(cls, status, params, charset):
    s = u"<html><body><h1>%s</h1><p>%s</p></body></html>" % \
      (xml_escape(params['name']), xml_escape(params['description']))
    return (charset, s.encode(charset))
  

codecs.register(codec)

if __name__ == '__main__':
  from datetime import datetime
  s = codec.encode({
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
  })
  print s
