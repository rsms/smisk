# encoding: utf-8
# Copyright (c) 2008, Eric Moritz <eric@themoritzfamily.com>
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
#   * Redistributions of source code must retain the above copyright
#   * notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above
#   * copyright notice, this list of conditions and the following
#   * disclaimer in the documentation and/or other materials provided
#   * with the distribution.  Neither the name of the <ORGANIZATION>
#   * nor the names of its contributors may be used to endorse or
#   * promote products derived from this software without specific
#   * prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''
This module provides a way to use Smisk as a WSGI backend.

Conforms to :pep:`333`

Example::

  def hello_app(env, start_response):
    start_response("200 OK", [])
    return ["Hello, World"]
  from smisk.wsgi import main
  main(hello_app)

:author: Eric Moritz
:author: Rasmus Andersson
'''
import os, sys, smisk.core, logging
from smisk.util.main import *
from smisk.config import LOGGING_FORMAT, LOGGING_DATEFMT

__all__ = ['__version__', 'Request', 'Gateway', 'main']
__version__ = (0,1,0)
_hop_headers = {
  'connection':1, 'keep-alive':1, 'proxy-authenticate':1,
  'proxy-authorization':1, 'te':1, 'trailers':1, 'transfer-encoding':1,
  'upgrade':1
}

def is_hop_by_hop(header_name):
  '''Return true if 'header_name' is an HTTP/1.1 "Hop-by-Hop" header'''
  return header_name.lower() in _hop_headers

class Request(smisk.core.Request):
  '''WSGI request'''
  def prepare(self, app):
    '''Set up the environment for one request'''
    self.env['wsgi.input']        = self.input
    self.env['wsgi.errors']       = self.errors
    self.env['wsgi.version']      = app.wsgi_version
    self.env['wsgi.run_once']     = app.wsgi_run_once
    self.env['wsgi.url_scheme']   = app.request.url.scheme
    self.env['wsgi.multithread']  = app.wsgi_multithread
    self.env['wsgi.multiprocess'] = app.wsgi_multiprocess
    
    # Put a reference of ourselves in the environment so that the user
    # might reference other parts of the framework and discover if they
    # are running in Smisk or not.
    self.env['smisk.app'] = app
    
    # Rebind our send_file to the real send_file
    self.send_file = app.response.send_file
  
  def send_file(self, path):
    raise NotImplementedError('unprepared request does not have a valid send_file method')
  

class Gateway(smisk.core.Application):
  '''WSGI adapter
  '''
  # Configuration parameters; can override per-subclass or per-instance
  wsgi_version = (1,0)
  wsgi_multithread = False
  wsgi_multiprocess = True
  wsgi_run_once = False
  
  def __init__(self, wsgi_app):
    super(Gateway, self).__init__()
    self.request_class = Request
    self.wsgi_app = wsgi_app
  
  def start_response(self, status, headers, exc_info=None):
    '''`start_response()` callable as specified by 
    `PEP 333 <http://www.python.org/dev/peps/pep-0333/>`__'''
    if exc_info:
      try:
        if self.response.has_begun:
          raise exc_info[0],exc_info[1],exc_info[2]
        else:
          # In this case of response not being initiated yet, this will replace 
          # both headers and any buffered body.
          self.error(exc_info[0], exc_info[1], exc_info[2])
      finally:
        exc_info = None # Avoid circular ref.
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
    self.response.headers = ['Status: '+status]
    # Append each of the headers provided by wsgi
    self.response.headers += [": ".join(header) for header in headers]
    # Add the X-Powered-By header to show off this extension
    self.response.headers.append("X-Powered-By: smisk+wsgi/%d.%d.%d" % __version__)
    # Return the write function as required by the WSGI spec
    return self.response.write
  
  def service(self):
    self.request.prepare(self)
    output = self.wsgi_app(self.request.env, self.start_response)
    # Discussion about Content-Length:
    #  Output might be an iterable in which case we can not trust len()
    #  but in a perfect world, we did know how many parts we got and if
    #  we only got _one_ we could also add a Content-length. But no.
    #  Instead, we rely on the host server splitting up things in nice
    #  chunks, using chunked transfer encoding, (If the server complies
    #  to HTTP/1.1 it is required to do so, so we are pretty safe) or
    #  simply rely on the host server setting the Content-Length header.
    for data in output:
      self.response.write(data)
  

# XXX TODO replace this main function with the stuff from smisk.util.main
def main(wsgi_app, appdir=None, bind=None, forks=None, handle_errors=True, cli=True):
  '''Helper for setting up and running an application.
  
  This is normally what you do in your top module ``__init__``::
  
    from smisk.wsgi import main
    from your.app import wsgi_app
    main(wsgi_app)
  
  Your module is now a runnable program which automatically configures and
  runs your application. There is also a Command Line Interface if `cli` 
  evaluates to ``True``.
  
  :Parameters:
    wsgi_app : callable
      A WSGI application
    appdir : string
      Path to the applications base directory.
    bind : string
      Bind to address (and port). Note that this overrides ``SMISK_BIND``.
    forks : int
      Number of child processes to spawn.
    handle_errors : bool
      Handle any errors by wrapping calls in `handle_errors_wrapper()`
    cli : bool
      Act as a *Command Line Interface*, parsing command line arguments and
      options.
  
  :rtype: None
  '''
  if cli:
    appdir, bind, forks = main_cli_filter(appdir=appdir, bind=bind, forks=forks)
  
  # Setup logging
  # Calling basicConfig has no effect if logging is already configured.
  
  logging.basicConfig(format=LOGGING_FORMAT, datefmt=LOGGING_DATEFMT)
  
  # Bind
  if bind is not None:
    os.environ['SMISK_BIND'] = bind
  if 'SMISK_BIND' in os.environ:
    smisk.core.bind(os.environ['SMISK_BIND'])
    log.info('Listening on %s', smisk.core.listening())
  
  # Configure appdir
  setup_appdir(appdir)
  
  # Forks
  if isinstance(forks, int) and forks > -1:
    application.forks = forks
  
  # Create the application
  application = Gateway(wsgi_app=wsgi_app)
  
  # Runloop
  if handle_errors:
    return handle_errors_wrapper(application.run)
  else:
    return application.run()



if __name__ == '__main__':
  from wsgiref.validate import validator # Import the wsgi validator app

  def hello_app(env, start_response):
    start_response("200 OK", [('Content-Type', 'text/plain')])
    return ["Hello, World"]
  
  if len(sys.argv) != 2:
    print "Usage: %s hostname:port" % (sys.argv[0])
    print "This runs a sample fastcgi server under the hostname and"
    print "port given in argv[1]"

  smisk.core.bind(sys.argv[1])

  app = validator(hello_app)
  Gateway(app).run()
