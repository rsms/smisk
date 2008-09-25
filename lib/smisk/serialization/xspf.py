# encoding: utf-8
'''
XSPF v1.0 serialization.

:Specification: http://xspf.org/xspf-v1.html
'''
import re, logging
from smisk.serialization import serializers, BaseSerializer
from smisk.core.xml import escape as xml_escape
from smisk.util import to_bool
from xml.dom.minidom import getDOMImplementation, parseString as parse_xml

DOM = getDOMImplementation()
log = logging.getLogger(__name__)

class ElementSpec(object):
  def __init__(self, name, desc=None, mincount=0, maxcount=1, typ=basestring, childspecs=[]):
    self.name = name
    self.mincount = mincount
    self.maxcount = maxcount
    self.typ = typ
    self.childspecs = childspecs
    self.desc = desc
  

class Serializer(BaseSerializer):
  '''XSPF serializer'''
  extensions = ('xspf',)
  media_types = ('application/xspf+xml',)
  encoding = 'utf-8'
  
  # Options
  pretty_print = False
  
  # Setup by setup
  ELEMENTS = {}
  
  @classmethod
  def encode(cls, **params):
    doc = DOM.createDocument('http://xspf.org/ns/0/', "playlist", None)
    root = doc.documentElement
    root.setAttribute('xmlns', 'http://xspf.org/ns/0/')
    root.setAttribute('version', '1.0')
    for k,v in params.items():
      if k == 'trackList':
        root.appendChild(cls.encode_trackList(doc, v))
      elif k in cls.ELEMENTS:
        n = doc.createElement(k)
        if v is not None:
          n.appendChild(doc.createTextNode(str(v)))
        root.appendChild(n)
      # else just skip the kv
    pretty_print = params.get('pretty_print', None)
    if (pretty_print is None and cls.pretty_print) or to_bool(pretty_print):
      return doc.toprettyxml('  ', encoding=cls.encoding)
    else:
      return doc.toxml(encoding=cls.encoding)
  
  @classmethod
  def encode_trackList(cls, doc, tracks):
    trackList = doc.createElement('trackList')
    if tracks:
      for t in tracks:
        track = doc.createElement('track')
        for k,v in t.items():
          n = doc.createElement(k)
          n.appendChild(doc.createTextNode(str(v)))
          track.appendChild(n)
        trackList.appendChild(track)
    return trackList
  
  @classmethod
  def encode_error(cls, status, params, typ, val, tb):
    from smisk.core import Application
    app = Application.current
    if app:
      identifier = str(Application.current.request.url) + '#'
    else:
      identifier = 'urn:smisk:'
    identifier += 'error/%d' % status.code
    return cls.encode(**{
      'title': status.name,
      'annotation': params.get('message', str(val)),
      'identifier': identifier,
      'trackList': None
    })
  
  INT_ELEMENTS_OF_TRACK = ('trackNum', 'duration')
  
  @classmethod
  def decode_trackList(cls, doc, trackList):
    tracks = []
    for track_node in trackList.childNodes:
      if track_node.nodeType is not doc.ELEMENT_NODE:
        continue
      track = {}
      for n in track_node.childNodes:
        if n.nodeType is not doc.ELEMENT_NODE:
          continue
        k = n.nodeName
        v = n.firstChild.nodeValue.strip()
        if k in cls.INT_ELEMENTS_OF_TRACK:
          v = int(v)
        track[str(k)] = v
      tracks.append(track)
    return tracks
  
  @classmethod
  def decode(cls, file, length=-1):
    ''':returns: (list args, dict params)'''
    doc = parse_xml(file.read(length))
    d = {}
    playlist = doc.firstChild
    for n in playlist.childNodes:
      if n.nodeType is not doc.ELEMENT_NODE:
        continue
      k = n.nodeName
      v = None
      if k == 'trackList':
        v = cls.decode_trackList(doc, n)
      else:
        v = n.firstChild.nodeValue.strip()
      d[str(k)] = v
    return (None, d)
  
  @classmethod
  def setup(cls):
    _E = ElementSpec
    tree = [
      _E('title', 'A human-readable title for the playlist.'),
      _E('creator', 'Human-readable name of the entity (author, authors, '\
        'group, company, etc) that authored the playlist.'),
      _E('annotation', 'A human-readable comment on the playlist. This is character '\
        'data, not HTML, and it may not contain markup.'),
      _E('info', 'URI of a web page to find out more about this playlist. Likely '\
        'to be homepage of the author, and would be used to find out more '\
        'about the author and to find more playlists by the author.'),
      _E('location', 'Source URI for this playlist.'),
      _E('identifier', 'Canonical ID for this playlist. Likely to be a hash or other '\
        'location-independent name. MUST be a legal URI.'),
      _E('image', 'URI of an image to display in the absence of a '\
        '//playlist/trackList/image element.'),
      _E('date', 'Creation date (not last-modified date) of the playlist, '\
        'formatted as a XML schema dateTime.'),
      _E('license', 'URI of a resource that describes the license under which this '\
        'playlist was released'),
      _E('attribution', 'An ordered list of URIs. The purpose is to satisfy licenses '\
        'allowing modification but requiring attribution.'),
      _E('link', 'The link element allows XSPF to be extended without the use of '\
        'XML namespaces.',
        maxcount=0),
      _E('meta', 'The meta element allows metadata fields to be added to XSPF.',
        maxcount=0),
      _E('extension', 'The extension element allows non-XSPF XML to be included in XSPF '\
        'documents. The purpose is to allow nested XML, which the meta and '\
        'link elements do not.',
        maxcount=0),
      _E('trackList', 'Ordered list of xspf:track elements to be rendered. The sequence '\
        'is a hint, not a requirement; renderers are advised to play tracks '\
        'from top to bottom unless there is an indication otherwise.',
        mincount=1),
    ]
    for e in tree:
      cls.ELEMENTS[e.name] = e
  

Serializer.setup()
serializers.register(Serializer)

if __name__ == '__main__':
  Serializer.pretty_print = True
  try:
    raise Exception('Mosmaster!')
  except:
    import sys
    from smisk.mvc.http import InternalServerError
    #print Serializer.encode_error(InternalServerError, {}, *sys.exc_info())
  xml = Serializer.encode(**{
    'title': 'Spellistan frum hell',
    'creator': 'rasmus',
    'trackList': [
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
    ]
  })
  #print xml
  from StringIO import StringIO
  f = StringIO(xml)
  print Serializer.decode(f)
