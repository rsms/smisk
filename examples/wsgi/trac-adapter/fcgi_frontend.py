#!/usr/bin/env python
# encoding: utf-8
#
# Trac FastCGI adapter backed by Smisk
# http://python-smisk.org/ 
#
# Author: Rasmus Andersson <rasmus@flajm.com>

from trac import __version__ as VERSION
from trac.web.main import dispatch_request
from smisk.wsgi import Gateway

def main():
  Gateway(dispatch_request).run()

if __name__ == '__main__':
  import pkg_resources
  pkg_resources.require('Trac==%s' % VERSION)
  main()
