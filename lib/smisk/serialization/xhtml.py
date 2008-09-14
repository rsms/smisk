# encoding: utf-8
'''
JSON serialization (RFC 4627)
'''
from . import serializers, BaseSerializer
from ..mvc import http
from smisk.core.xml import escape as xml_escape

def doc(title, body):
  v = ['<?xml version="1.0" encoding="%s" ?>' % Serializer.encoding]
  v.append('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" '\
           '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">')
  v.append('<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">')
  v.append('<head><title>%s</title></head>' % xml_escape(title))
  v.append('<body>')
  v.extend(body)
  v.append('</body>')
  v.append('</html>')
  return "\n".join(v)


class Serializer(BaseSerializer):
  '''XHTML Serializer'''
  extension = 'html'
  media_type = 'application/xhtml+xml'
  encoding = 'utf-8'
    
  @classmethod
  def encode(cls, **params):
    body = ['<h1>Parameters:</h1><ol>']
    body.extend(['<li><b>%s:</b> <tt>%s</tt></li>' \
      % (xml_escape(str(k)), xml_escape(str(v))) for k,v in params.items()])
    body.append('</ol>')
    return doc('Response', body)
  
  @classmethod
  def encode_error(cls, typ, val, tb):
    message = str(val)
    status = getattr(val, 'http_code', 500)
    if status in http.STATUS:
      status = str(http.STATUS[status])
    else:
      status = '%d Internal Server Error' % status
    return doc(status, ["<html><body><h1>%s</h1><p>%s</p></body></html>" \
               % (status, message)]) 
  

serializers.register(Serializer, ['text/html'])
