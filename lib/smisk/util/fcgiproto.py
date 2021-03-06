# encoding: utf-8

class FastCGIError(Exception):
  pass

# Values for type component of FCGI_Header

FCGI_BEGIN_REQUEST     = 1
FCGI_ABORT_REQUEST     = 2
FCGI_END_REQUEST     = 3
FCGI_PARAMS        = 4
FCGI_STDIN         = 5
FCGI_STDOUT        = 6
FCGI_STDERR        = 7
FCGI_DATA        = 8
FCGI_GET_VALUES      = 9
FCGI_GET_VALUES_RESULT   = 10
FCGI_UNKNOWN_TYPE    = 11

typeNames = {
  FCGI_BEGIN_REQUEST  : 'fcgi_begin_request',
  FCGI_ABORT_REQUEST  : 'fcgi_abort_request',
  FCGI_END_REQUEST    : 'fcgi_end_request',
  FCGI_PARAMS       : 'fcgi_params',
  FCGI_STDIN      : 'fcgi_stdin',
  FCGI_STDOUT       : 'fcgi_stdout',
  FCGI_STDERR       : 'fcgi_stderr',
  FCGI_DATA       : 'fcgi_data',
  FCGI_GET_VALUES     : 'fcgi_get_values',
  FCGI_GET_VALUES_RESULT: 'fcgi_get_values_result',
  FCGI_UNKNOWN_TYPE   : 'fcgi_unknown_type'}

# Mask for flags component of FCGI_BeginRequestBody
FCGI_KEEP_CONN = 1

# Values for role component of FCGI_BeginRequestBody
FCGI_RESPONDER  = 1
FCGI_AUTHORIZER = 2
FCGI_FILTER   = 3

# Values for protocolStatus component of FCGI_EndRequestBody

FCGI_REQUEST_COMPLETE = 0
FCGI_CANT_MPX_CONN  = 1
FCGI_OVERLOADED     = 2
FCGI_UNKNOWN_ROLE   = 3

FCGI_MAX_PACKET_LEN = 0xFFFF

class Record(object):
  def __init__(self, type, reqId, content='', version=1):
    self.version = version
    self.type = type
    self.reqId = reqId
    self.content = content
    self.length = len(content)
    if self.length > FCGI_MAX_PACKET_LEN:
      raise ValueError("Record length too long: %d > %d" %
               (self.length, FCGI_MAX_PACKET_LEN))
    if self.length % 8 != 0:
      self.padding = 8 - (self.length & 7)
    else:
      self.padding = 0
    self.reserved = 0
    
  def fromHeaderString(clz, rec):
    self = object.__new__(clz)
    self.version = ord(rec[0])
    self.type = ord(rec[1])
    self.reqId = (ord(rec[2])<<8)|ord(rec[3])
    self.length = (ord(rec[4])<<8)|ord(rec[5])
    self.padding = ord(rec[6])
    self.reserved = ord(rec[7])
    self.content = None
    return self
  
  fromHeaderString = classmethod(fromHeaderString)

  def toOutputString(self):
    return "%c%c%c%c%c%c%c%c" % (
      self.version, self.type,
      (self.reqId&0xFF00)>>8, self.reqId&0xFF,
      (self.length&0xFF00)>>8, self.length & 0xFF,
      self.padding, self.reserved) + self.content + '\0'*self.padding
    
  def totalLength(self):
    return 8 + self.length + self.padding

  def __repr__(self):
    return "<FastCGIRecord version=%d type=%d(%s) reqId=%d>" % (
      self.version, self.type, typeNames.get(self.type), self.reqId)
  
def parseNameValues(s):
  '''
  @param s: String containing valid name/value data, of the form:
        'namelength + valuelength + name + value' repeated 0 or more
        times. See C{fastcgi.writeNameValue} for how to create this
        string.
  @return: Generator of tuples of the form (name, value)
  '''
  off = 0
  while off < len(s):
    nameLen = ord(s[off])
    off += 1
    if nameLen&0x80:
      nameLen=(nameLen&0x7F)<<24 | ord(s[off])<<16 | ord(s[off+1])<<8 | ord(s[off+2])
      off += 3
    valueLen=ord(s[off])
    off += 1
    if valueLen&0x80:
      valueLen=(valueLen&0x7F)<<24 | ord(s[off])<<16 | ord(s[off+1])<<8 | ord(s[off+2])
      off += 3
    yield (s[off:off+nameLen], s[off+nameLen:off+nameLen+valueLen])
    off += nameLen + valueLen

def getLenBytes(length):
  if length<0x80:
    return chr(length)
  elif 0 < length <= 0x7FFFFFFF:
    return (chr(0x80|(length>>24)&0x7F) + chr((length>>16)&0xFF) + 
        chr((length>>8)&0xFF) + chr(length&0xFF))
  else:
    raise ValueError("Name length too long.")

def writeNameValue(name, value):
  return getLenBytes(len(name)) + getLenBytes(len(value)) + name + value

class Channel(object):
  maxConnections = 100
  reqId = 0
  request = None
  
  ## High level protocol
  def packetReceived(self, packet):
    '''
    @param packet: instance of C{fastcgi.Record}.
    @raise: FastCGIError on invalid version or where the type does not exist
        in funName
    '''
    if packet.version != 1:
      raise FastCGIError("FastCGI packet received with version != 1")
    
    funName = typeNames.get(packet.type)
    if funName is None:
      raise FastCGIError("Unknown FastCGI packet type: %d" % packet.type)
    getattr(self, funName)(packet)

  def fcgi_get_values(self, packet):
    if packet.reqId != 0:
      raise ValueError("Should be 0!")
    
    content = ""
    for name,value in parseNameValues(packet.content):
      outval = None
      if name == "FCGI_MAX_CONNS":
        outval = str(self.maxConnections)
      elif name == "FCGI_MAX_REQS":
        outval = str(self.maxConnections)
      elif name == "FCGI_MPXS_CONNS":
        outval = "0"
      if outval:
        content += writeNameValue(name, outval)
    self.writePacket(Record(FCGI_GET_VALUES_RESULT, 0, content))
  
  def fcgi_unknown_type(self, packet):
    # Unused, reserved for future expansion
    pass

  def fcgi_begin_request(self, packet):
    role = ord(packet.content[0])<<8 | ord(packet.content[1])
    flags = ord(packet.content[2])
    if packet.reqId == 0:
      raise ValueError("ReqId shouldn't be 0!")
    if self.reqId != 0:
      self.writePacket(Record(FCGI_END_REQUEST, self.reqId,
                  "\0\0\0\0"+chr(FCGI_CANT_MPX_CONN)+"\0\0\0"))
    if role != FCGI_RESPONDER:
      self.writePacket(Record(FCGI_END_REQUEST, self.reqId,
                  "\0\0\0\0"+chr(FCGI_UNKNOWN_ROLE)+"\0\0\0"))
    
    self.reqId = packet.reqId
    self.keepalive = flags & FCGI_KEEP_CONN
    self.params = ""
    
  def fcgi_abort_request(self, packet):
    if packet.reqId != self.reqId:
      return

    self.request.connectionLost()
    
  def fcgi_params(self, packet):
    if packet.reqId != self.reqId:
      return
    
    # I don't feel like doing the work to incrementally parse this stupid
    # protocol, so we'll just buffer all the params data before parsing.
    if not packet.content:
      self.makeRequest(dict(parseNameValues(self.params)))
      self.request.process()
    self.params += packet.content
    
  def fcgi_stdin(self, packet):
    if packet.reqId != self.reqId:
      return
    
    if not packet.content:
      self.request.handleContentComplete()
    else:
      self.request.handleContentChunk(packet.content)
    
  def fcgi_data(self, packet):
    # For filter roles only, which is currently unsupported.
    pass

  def write(self, data):
    if len(data) > FCGI_MAX_PACKET_LEN:
      n = 0
      while 1:
        d = data[n*FCGI_MAX_PACKET_LEN:(n+1)*FCGI_MAX_PACKET_LEN]
        if not d:
          break
        self.write(d)
      return
    
    self.writePacket(Record(FCGI_STDOUT, self.reqId, data))
    
  def writeHeaders(self, code, headers):
    l = []
    code_message = responsecode.RESPONSES.get(code, "Unknown Status")
    
    l.append("Status: %s %s\n" % (code, code_message))
    if headers is not None:
      for name, valuelist in headers.getAllRawHeaders():
        for value in valuelist:
          l.append("%s: %s\n" % (name, value))
    l.append('\n')
    self.write(''.join(l))

  def finish(self):
    if self.request is None:
      raise RuntimeError("Request.finish called when no request was outstanding.")
    self.writePacket(Record(FCGI_END_REQUEST, self.reqId,
                "\0\0\0\0"+chr(FCGI_REQUEST_COMPLETE)+"\0\0\0"))
    del self.reqId, self.request
    if not self.keepalive:
      self.transport.loseConnection()
    
## Low level protocol
  paused = False
  _lastRecord = None
  recvd = ""
  
  def writePacket(self, packet):
    data = packet.toOutputString()
    #print "Writing record", packet, repr(data)
    self.sock.sendall(data)
  
  def read(self, length):
    s = ''
    while len(s) < length:
      s = self.sock.recv(length-len(s))
    return s
  
  def readPacket(self, tryrecv=False):
    if tryrecv:
      try:
        self.sock.setblocking(0)
        s = self.sock.recv(8)
      finally:
        self.sock.setblocking(1)
      if len(s) < 8:
        s += self.read(8-len(s))
    else:
      s = self.read(8)
    record = Record.fromHeaderString(s)
    if record.length:
      record.content = self.read(record.length)
    if record.padding:
      self.read(record.padding)
    return record
  
  def dataReceived(self, recd):
    self.recvd = self.recvd + recd
    record = self._lastRecord
    self._lastRecord = None
    while len(self.recvd) >= 8 and not self.paused:
      if record is None:
        record = Record.fromHeaderString(self.recvd[:8])
      if len(self.recvd) < record.totalLength():
        self._lastRecord = record
        break
      record.content = self.recvd[8:record.length+8]
      self.recvd = self.recvd[record.totalLength():]
      self.packetReceived(record)
      record = None

  def pauseProducing(self):
    self.paused = True
    self.transport.pauseProducing()

  def resumeProducing(self):
    self.paused = False
    self.transport.resumeProducing()
    self.dataReceived('')

  def stopProducing(self):
    self.paused = True
    self.transport.stopProducing()

