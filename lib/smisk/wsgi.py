"""This module provides a way to tie Smisk to a wsgi app

Copyright (c) 2008, Eric Moritz <eric@themoritzfamily.com>
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

  * Redistributions of source code must retain the above copyright
  * notice, this list of conditions and the following disclaimer.
  * Redistributions in binary form must reproduce the above
  * copyright notice, this list of conditions and the following
  * disclaimer in the documentation and/or other materials provided
  * with the distribution.  Neither the name of the <ORGANIZATION>
  * nor the names of its contributors may be used to endorse or
  * promote products derived from this software without specific
  * prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
import smisk

__version__ = '0.1.0'

_hop_headers = {
  'connection':1, 'keep-alive':1, 'proxy-authenticate':1,
  'proxy-authorization':1, 'te':1, 'trailers':1, 'transfer-encoding':1,
  'upgrade':1
}

def is_hop_by_hop(header_name):
  """Return true if 'header_name' is an HTTP/1.1 "Hop-by-Hop" header"""
  return header_name.lower() in _hop_headers

def guess_scheme(environ):
  """Return a guess for whether 'wsgi.url_scheme' should be 'http' or 'https'
  """
  if environ.get("HTTPS") in ('yes','on','1'):
    return 'https'
  else:
    return 'http'

class SmiskWSGI(smisk.Application):
  """This is the Smisk Wsgi adapter."""
  # Configuration parameters; can override per-subclass or per-instance
  wsgi_version = (1,0)
  wsgi_multithread = True
  wsgi_multiprocess = True
  wsgi_run_once = False

  def __init__(self, wsgi_app):
    self.wsgi_app = wsgi_app

  def get_scheme(self):
    """Return the URL scheme being used"""
    return guess_scheme(self.request.env)

  def start_response(self, status, headers,exc_info=None):
    """'start_response()' callable as specified by PEP 333"""
    if exc_info:
      try:
        if self.response.has_begun():
          # Call the application's error call, not sure
          # what smisk does with this.
          self.error(exc_info[0], exc_info[1], exc_info[2])
      finally:
        exc_info = None    # avoid dangling circular ref
    elif len(self.response.headers) != 0:
      raise AssertionError("Headers already set!")

    assert isinstance(status, str),"Status must be a string"
    assert len(status)>=4,"Status must be at least 4 characters"
    assert int(status[:3]),"Status message must begin w/3-digit code"
    assert status[3]==" ", "Status message must have a space after code"

    if __debug__:
      for name,val in headers:
        assert isinstance(name, str),"Header names must be strings"
        assert isinstance(val, str),"Header values must be strings"
        assert not is_hop_by_hop(name),"Hop-by-hop headers not allowed"
    
    # Construct the headers
    # Add the status to the headers
    self.response.headers = [status]
    # Append each of the headers provided by wsgi
    self.response.headers += [": ".join(header) for header in headers]
    # Add the X-Powered-By header to show off Smisk
    self.response.headers.append("X-Powered-By: smisk/%s smisk+wsgi/%s" %
      (smisk.__version__, __version__))
    # Return the write function as required by the WSGI spec
    return self.response.write

  def init_request(self):
    """Set up the environment for one request"""
    self.request.env['wsgi.input']    = self.request.input
    self.request.env['wsgi.errors']     = self.request.err
    self.request.env['wsgi.version']    = self.wsgi_version
    self.request.env['wsgi.run_once']   = self.wsgi_run_once
    self.request.env['wsgi.url_scheme']   = self.get_scheme()
    self.request.env['wsgi.multithread']  = self.wsgi_multithread
    self.request.env['wsgi.multiprocess'] = self.wsgi_multiprocess

    # Put a reference of ourselves in the environment so that they
    # could access self.response.send_file if they want
    self.request.env['smisk.app'] = self

  def service(self):
    self.init_request()
    output = self.wsgi_app(self.request.env, self.start_response)
    for data in output: 
      self.response.write(data)


def hello_app(env, start_response):
  start_response("200 OK", [])
  return ["Hello, World"]

if __name__ == '__main__':
  import sys
  if len(sys.argv) != 2:
    print "Usage: %s hostname:port" % (sys.argv[0])
    print "This runs a sample fastcgi server under the hostname and"
    print "port given in argv[1]"

  smisk.bind(sys.argv[1])
  SmiskWSGI(hello_app).run()
