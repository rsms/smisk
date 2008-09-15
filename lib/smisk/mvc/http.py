# encoding: utf-8
from ..util import normalize_url

STATUS = {}

class HTTPExc(Exception):
  def __init__(self, status, *args, **kwargs):
    super(HTTPExc, self).__init__()
    self.status = status
    self.args = args
    self.kwargs = kwargs
  
  def __call__(self, app):
    return self.status.service(app, *self.args, **self.kwargs)
  

class Status(object):
  def __init__(self, code, name):
    self.code = code
    self.name = name
    STATUS[code] = self
  
  def __call__(self, *args, **kwargs):
    return HTTPExc(self, *args, **kwargs)
  
  def service(self, app, *args, **kwargs):
    app.response.status = self
    app.response.headers = [] # clear any previous headers
    return {
      'status': {
        'code': self.code,
        'name': self.name
      },
      'message': ''
    }
  
  @property
  def is_error(self):
    return self.code % 500 < 100
  
  def __str__(self):
    return '%d %s' % (self.code, self.name)
  
  def __repr__(self):
    return 'Status(%d, %s)' % (self.code, repr(self.name))
  


class Status300(Status):
  def service(self, app, url, *args, **kwargs):
    rsp = Status.service(self, app)
    app.response.headers = ['Location: ' + normalize_url(url)]
    rsp.update({
      'message': 'The resource has moved'
    })
    return rsp
  

class Status404(Status):
  def service(self, app, url, *args, **kwargs):
    rsp = Status.service(self, app)
    rsp['message'] = 'No resource exists at %s' % app.request.url.path
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
PaymentRequired              = Status(402, "Payment Required")
Forbidden                    = Status(403, "Forbidden")
NotFound                     = Status404(404, "Not Found")

ControllerNotFound           = Status404(404, "Not Found")
MethodNotFound               = Status404(404, "Not Found")
TemplateNotFound             = Status404(404, "Not Found")

MethodNotAllowed             = Status(405, "Method Not Allowed")
NotAcceptable                = Status(406, "Not Acceptable")
ProxyAuthenticationRequired  = Status(407, "Proxy Authentication Required")
RequestTimeout               = Status(408, "Request Time-out")
Conflict                     = Status(409, "Conflict")
Gone                         = Status(410, "Gone")
LengthRequired               = Status(411, "Length Required")
PreconditionFailed           = Status(412, "Precondition Failed")
RequestEntityTooLarge        = Status(413, "Request Entity Too Large")
RequestURITooLarge           = Status(414, "Request-URI Too Large")
UnsupportedMediaType         = Status(415, "Unsupported Media Type")
RequestedRangeNotSatisfiable = Status(416, "Requested range not satisfiable")
ExpectationFailed            = Status(417, "Expectation Failed")

InternalServerError          = Status(500, "Internal Server Error")
NotImplemented               = Status(501, "Not Implemented")
BadGateway                   = Status(502, "Bad Gateway")
ServiceUnavailable           = Status(503, "Service Unavailable")
GatewayTimeout               = Status(504, "Gateway Time-out")
HTTPVersionNotSupported      = Status(505, "HTTP Version not supported")
