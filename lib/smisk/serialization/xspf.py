# encoding: utf-8
'''XSPF v1.0 serialization.

:see: `XSPF v1.0 <http://xspf.org/xspf-v1.html>`__
'''
import base64
from smisk.serialization.xmlbase import *
from datetime import datetime
from smisk.util.DateTime import DateTime
from types import *
try:
  from xml.etree.ElementTree import QName
except ImportError:
  pass

__all__ = [
  'XSPFSerializationError',
  'XSPFUnserializationError',
  'XSPFSerializer']

class XSPFSerializationError(XMLSerializationError):
  pass

class XSPFUnserializationError(XMLUnserializationError):
  pass

class XSPFSerializer(XMLSerializer):
  '''XML Property List serializer
  '''
  name = 'XSPF: XML Shareable Playlist Format'
  extensions = ('xspf',)
  media_types = ('application/xspf+xml',)
  charset = 'utf-8'  
  
  xml_default_ns = 'http://xspf.org/ns/0/'
  xml_root_name = 'playlist'
  xml_root_attrs = {'version':'1.0'}
  
  BASE_TAGS = (
    'title',
    'creator',
    'annotation',
    'info',
    'location',
    'identifier',
    'image',
    'date',
    'license',
    'attribution',
    'link',
    'meta',
    'extension',
    'trackList',
  )
  TRACK_TEXT_TAGS = (
    'location',
    'identifier',
    'title',
    'creator',
    'annotation',
    'info',
    'image',
    'album',
  )
  TRACK_INT_TAGS = (
    'trackNum',
    'duration',
  )
  TRACK_XML_TAGS = (
    'extension',
  )
  TRACK_META_TAGS = (
    'link',
    'content',
  )
  
  # Reading
  
  @classmethod
  def parse_document(cls, elem):
    playlist = {}
    for child in elem.getchildren():
      k,ns = cls.xml_tag(child)
      if k == 'trackList':
        v = cls.parse_trackList(child)
      elif k == 'date':
        v = DateTime.parse_xml_schema_dateTime(child.text)
      elif k in cls.BASE_TAGS:
        v = child.text
      playlist[k] = v
    return playlist
  
  @classmethod
  def parse_trackList(cls, elem):
    tracks = []
    for child in elem.getchildren():
      if cls.xml_tag(child)[0] == 'track':
        tracks.append(cls.parse_track(child))
    return tracks
  
  @classmethod
  def parse_track(cls, elem):
    track = {}
    for child in elem.getchildren():
      k,ns = cls.xml_tag(child)
      if k in cls.TRACK_TEXT_TAGS:
        track[k] = child.text
      elif k in cls.TRACK_INT_TAGS:
        track[k] = int(child.text)
      elif k in cls.TRACK_META_TAGS:
        track[k] = cls.prase_track_meta(child)
      elif k in cls.TRACK_XML_TAGS:
        track[k] = child
    return track
  
  @classmethod
  def parse_track_meta(cls, elem):
    return {
      'rel':elem.get('rel'),
      'content':elem.text
    }
  
  # Writing
  
  @classmethod
  def build_document(cls, obj):
    root = Element(cls.xml_root_name, **cls.xml_root_attrs)
    for k,v in obj.iteritems():
      if k == 'trackList':
        root.append(cls.build_trackList(v))
      else:
        if isinstance(v, datetime):
          v = DateTime(v).as_utc().strftime('%Y-%m-%dT%H:%M:%SZ')
        elif not isinstance(v, basestring):
          v = str(v)
        root.append(cls.xml_mktext(k, v))
    return root
  
  @classmethod
  def build_trackList(cls, iterable):
    e = Element('trackList')
    for track in iterable:
      e.append(cls.build_track(track))
    return e
  
  @classmethod
  def build_track(cls, track):
    e = Element('track')
    for k,v in track.iteritems():
      if not isinstance(v, basestring):
        v = str(v)
      e.append(cls.xml_mktext(k, v))
    return e
  
  # Encoding errors
  
  @classmethod
  def serialize_error(cls, status, params, charset):
    from smisk.core import request
    if request:
      identifier = unicode(request.url) + u'#'
    else:
      identifier = u'smisk:'
    identifier += u'error:%d' % status.code
    return cls.encode({
      u'title':      params['name'],
      u'annotation': params['description'],
      u'identifier': identifier,
      u'trackList':  None
    }, charset)
  

# Only register if xml.etree is available
if ElementTree is not None:
  serializers.register(XSPFSerializer)

if __name__ == '__main__':
  if 0:
    try:
      raise Exception('Mosmaster!')
    except:
      import sys
      from smisk.mvc.http import InternalServerError
      print XSPFSerializer.serialize_error(InternalServerError, {}, 'utf-8')
  charset, xmlstr = XSPFSerializer.serialize({
    'title': 'Spellistan frum hell',
    'creator': 'rasmus',
    'date': DateTime.now(),
    'trackList': (
      {
        'location': 'spotify:track:0yR57jH25o1jXGP4T6vNGR',
        'identifier': 'spotify:track:0yR57jH25o1jXGP4T6vNGR',
        'title': 'Go Crazy (feat. Majida)',
        'creator': 'Armand Van Helden',
        'album': 'Ghettoblaster',
        'trackNum': 1,
        'duration': 410000
      },
      {
        'location': 'spotify:track:0yR57jH25o1jXGP4T6vNGR',
        'identifier': 'spotify:track:0yR57jH25o1jXGP4T6vNGR',
        'title': 'Go Crazy2 (feat. Majida)',
        'creator': 'Armand Van Helden2',
        'album': 'Ghettoblaster2',
        'trackNum': 2,
        'duration': 410002
      },
      {
        'location': 'spotify:track:0yR57jH25o1jXGP4T6vNGR',
        'identifier': 'spotify:track:0yR57jH25o1jXGP4T6vNGR',
        'title': 'Go Crazy3 (feat. Majida)',
        'creator': 'Armand Van Helden3',
        'album': 'Ghettoblaster3',
        'trackNum': 3,
        'duration': 410007
      },
    )
  }, 'utf-8')
  print xmlstr
  from StringIO import StringIO
  print repr(XSPFSerializer.unserialize(StringIO(xmlstr)))
