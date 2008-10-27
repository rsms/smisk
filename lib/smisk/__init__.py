# encoding: utf-8
'''
Simple, high-performance and scalable web service framework for FastCGI
– written in C, but controlled by Python.

More information on http://trac.hunch.se/smisk
'''

from smisk.release import version   as __version__, author  as __author__, \
                          license as __license__, copyright as __copyright__

import smisk.core
app = smisk.core.app
'See documentation for `smisk.core.app`'
request = smisk.core.request
'See documentation for `smisk.core.request`'
response = smisk.core.response
'See documentation for `smisk.core.response`'

__all__ = ['__version__', '__author__', '__license__', '__copyright__',
           'app', 'request', 'response']
