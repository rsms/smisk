# encoding: utf-8
'''Date and Time utilities
'''
import re, time
from datetime import datetime, timedelta, tzinfo
ZERO_TIMEDELTA = timedelta(0)

__all__ = ['UTCTimeZone', 'OffsetTimeZone', 'DateTime']

class UTCTimeZone(tzinfo):
  '''UTC
  '''
  def __new__(cls):
    try:
      return cls._instance
    except AttributeError:
      cls._instance = tzinfo.__new__(UTCTimeZone)
    return cls._instance
  
  def utcoffset(self, dt):
    return ZERO_TIMEDELTA
  
  def tzname(self, dt):
    return "UTC"
  
  def dst(self, dt):
    return ZERO_TIMEDELTA
  
  def __repr__(self):
    return 'UTCTimeZone()'
  

class OffsetTimeZone(tzinfo):
  '''Fixed offset in minutes east from UTC.
  '''
  def __init__(self, tzstr_or_minutes):
    if isinstance(tzstr_or_minutes, basestring):
      minutes = (int(tzstr_or_minutes[1:3]) * 60) + int(tzstr_or_minutes[4:6])
      if tzstr_or_minutes[0] == '-':
        minutes = -minutes
    else:
      minutes = tzstr_or_minutes
    self.__minute_offset = minutes
    self.__offset = timedelta(minutes=minutes)
  
  def utcoffset(self, dt):
    return self.__offset
  
  def dst(self, dt):
    return ZERO_TIMEDELTA
  
  def __repr__(self):
    return 'OffsetTimeZone(%d)' % self.__minute_offset
  

class DateTime(datetime):
  '''Time zone aware version of datetime with additional parsers.
  '''
  XML_SCHEMA_DATETIME_RE = re.compile(r'((?#year)-?\d{4})-((?#month)\d{2})-((?#day)\d{2})T'\
    r'((?#hour)\d{2}):((?#minute)\d{2}):((?#second)\d{2})((?#millis)\.\d+|)((?#tz)[+-]\d{2}:\d{2}|Z?)')
  '''XML schema dateTime regexp.
  
  :type: RegexType
  '''
  
  def __new__(cls, dt=None, *args, **kwargs):
    if isinstance(dt, datetime):
      if type(dt) is cls:
        return dt
      return datetime.__new__(cls, 
        dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond, dt.tzinfo)
    return datetime.__new__(cls, dt, *args, **kwargs)
  
  def as_utc(self):
    '''Return this date in Universal Time Coordinate
    '''
    if self.tzinfo is UTCTimeZone():
      return self
    offset = self.utcoffset()
    if offset is None:
      dt = self.replace(tzinfo=UTCTimeZone())
    else:
      dt = (self - offset).replace(tzinfo=UTCTimeZone())
    return DateTime(dt)
  
  @classmethod
  def now(self):
    if time.timezone == 0 and time.daylight == 0:
      tz = UTCTimeZone()
    else:
      tz = OffsetTimeZone(((-time.timezone)/60) + (time.daylight * 60))
    return datetime.now().replace(tzinfo=tz)
  
  @classmethod
  def parse_xml_schema_dateTime(cls, string):
    '''Parse a XML Schema dateTime value.
    
    :see: `XML Schema Part 2: Datatypes Second Edition, 3.2.7 dateTime
          <http://www.w3.org/TR/xmlschema-2/#dateTime>`__
    '''
    m = cls.XML_SCHEMA_DATETIME_RE.match(string).groups()
    if m[7] and m[7] != 'Z':
      tz = OffsetTimeZone(m[7])
    else:
      tz = UTCTimeZone()
    microsecond = 0
    if m[6]:
      microsecond = int(float(m[6]) * 1000000.0)
    dt = DateTime(int(m[0]), int(m[1]), int(m[2]), int(m[3]), int(m[4]), int(m[5]), microsecond, tz)
    return dt
  
