# encoding: utf-8
from smisk.util import normalize_url

STATUS = {}

class HTTPExc(Exception):
  def __init__(self, status, *args, **kwargs):
    super(HTTPExc, self).__init__()
    self.status = status
    self.args = args
    self.kwargs = kwargs
  
  def __call__(self, app):
    return self.status.service(app, *self.args, **self.kwargs)
  
  def __str__(self):
    return '%s %s %s' % (self.status, self.args, self.kwargs)
  

class Status(object):
  def __init__(self, code, name, has_body=True):
    self.code = code
    self.name = name
    self.has_body = has_body
    STATUS[code] = self
  
  def __call__(self, *args, **kwargs):
    return HTTPExc(self, *args, **kwargs)
  
  def service(self, app, *args, **kwargs):
    app.response.status = self
    app.response.headers = ['Status: %s' % self] # clear any previous headers
    if self.has_body:
      return {'code': self.code, 'description': self.name, 'http_error': True}
  
  @property
  def is_error(self):
    return self.code % 500 < 100
  
  def __str__(self):
    return '%d %s' % (self.code, self.name)
  
  def __repr__(self):
    return 'Status(%r, %r)' % (self.code, self.name)
  


class Status300(Status):
  def service(self, app, url=None, *args, **kwargs):
    if url is None:
      raise Exception('Status300 requires a 3:rd argument "url"')
    rsp = Status.service(self, app)
    app.response.headers.append('Location: ' + normalize_url(url))
    rsp['description'] = 'The resource has moved to %s' % url
    return rsp
  

class Status404(Status):
  def service(self, app, *args, **kwargs):
    rsp = Status.service(self, app)
    rsp['description'] = 'No resource exists at %s' % app.request.url.path
    return rsp
  

class StatusNotAcceptable(Status):
  def service(self, app, *args, **kwargs):
    rsp = Status.service(self, app)
    from smisk.codec import codecs
    # Note: Lighttpd 1.4 is confirmed not to send any body, so this will never be sent
    #       If running in lighttpd 1.4. The specification of this HTTP 1.1 status code
    #       is somewhat vauge but we interpret it as being able to contain a body.
    rsp['description'] = 'Acceptable types: %s' % ', '.join(codecs.media_types.keys())
    return rsp
  


Continue                     = Status(100, "Continue")
SwitchingProtocols           = Status(101, "Switching Protocols")

OK                           = Status(200, "OK")
Created                      = Status(201, "Created")
Accepted                     = Status(202, "Accepted")
NonAuthoritativeInformation  = Status(203, "Non-Authoritative Information")
NoContent                    = Status(204, "No Content")
ResetContent                 = Status(205, "Reset Content")
PartialContent               = Status(206, "Partial Content")

MultipleChoices              = Status300(300, "Multiple Choices")
MovedPermanently             = Status300(301, "Moved Permanently")
Found                        = Status300(302, "Found")
SeeOther                     = Status300(303, "See Other")
NotModified                  = Status300(304, "Not Modified")
UseProxy                     = Status300(305, "Use Proxy")
TemporaryRedirect            = Status300(307, "Temporary Redirect")

BadRequest                   = Status(400, "Bad Request")
Unauthorized                 = Status(401, "Unauthorized")
PaymentRequired              = Status(402, "Payment Required", False)
Forbidden                    = Status(403, "Forbidden")
NotFound                     = Status404(404, "Not Found")

ControllerNotFound           = Status404(404, "Not Found")
MethodNotFound               = Status404(404, "Not Found")
TemplateNotFound             = Status404(404, "Not Found")

MethodNotAllowed             = Status(405, "Method Not Allowed", False)
NotAcceptable                = StatusNotAcceptable(406, "Not Acceptable", False)
ProxyAuthenticationRequired  = Status(407, "Proxy Authentication Required", False)
RequestTimeout               = Status(408, "Request Time-out", False)
Conflict                     = Status(409, "Conflict", False)
Gone                         = Status(410, "Gone", False)
LengthRequired               = Status(411, "Length Required")
PreconditionFailed           = Status(412, "Precondition Failed")
RequestEntityTooLarge        = Status(413, "Request Entity Too Large")
RequestURITooLarge           = Status(414, "Request-URI Too Large")
UnsupportedMediaType         = Status(415, "Unsupported Media Type", False)
RequestedRangeNotSatisfiable = Status(416, "Requested range not satisfiable")
ExpectationFailed            = Status(417, "Expectation Failed")

InternalServerError          = Status(500, "Internal Server Error")
NotImplemented               = Status(501, "Not Implemented")
BadGateway                   = Status(502, "Bad Gateway")
ServiceUnavailable           = Status(503, "Service Unavailable")
GatewayTimeout               = Status(504, "Gateway Time-out")
HTTPVersionNotSupported      = Status(505, "HTTP Version not supported")
