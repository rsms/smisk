# encoding: utf-8
'''
JSON serialization (RFC 4627)
'''
from smisk.codec import codecs, BaseCodec
from smisk.mvc import http
from smisk.core.xml import escape as xml_escape
from smisk.core import Application

def doc(title, body):
  v = ['<?xml version="1.0" encoding="%s" ?>' % codec.encoding]
  v.append('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" '\
           '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">')
  v.append('<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">')
  v.append('<head><title>%s</title></head>' % xml_escape(title))
  v.append('<body>')
  v.extend(body)
  v.append('</body>')
  v.append('</html>')
  return "\n".join(v)


class codec(BaseCodec):
  '''XHTML codec'''
  extensions = ('html',)
  media_types = ('text/html', 'application/xhtml+xml')
  encoding = 'utf-8'
    
  @classmethod
  def encode(cls, **params):
    body = ['<h1>Parameters:</h1><ol>']
    body.extend(['<li><b>%s:</b> <tt>%s</tt></li>' \
      % (xml_escape(str(k)), xml_escape(str(v))) for k,v in params.items()])
    body.append('</ol>')
    title = 'XHTML response'
    if Application.current.destination is not None:
      '/'.join(Application.current.destination.path)
    return doc(title, body)
  
  @classmethod
  def encode_error(cls, status, params, typ, val, tb):
    message = str(val)
    if status in http.STATUS:
      status = str(http.STATUS[status])
    else:
      status = '%d Internal Server Error' % status
    return doc(status, ["<html><body><h1>%s</h1><p>%s</p></body></html>" \
               % (xml_escape(status), xml_escape(message))])
  

codecs.register(codec)
