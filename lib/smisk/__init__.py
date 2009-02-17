# encoding: utf-8
'''
Simple, high-performance and scalable web service framework for FastCGI
– written in C, but controlled by Python.

More information on http://trac.hunch.se/smisk
'''

from smisk.release import version   as __version__, author  as __author__, \
                          license as __license__, copyright as __copyright__
from _smisk import app, request, response, __build__

__all__ = ['__version__', '__author__', '__license__', '__copyright__','__build__',
           'app', 'request', 'response']

# XXX - the smisk.util.collections module shadow import of
# the system module collections, thus we perform the import here
# which is later picked up by smisk.util.type. Real ugly, yes.
# During the next minor version bumb (v1.2) we will probably rename
# the smisk.util.collections module thus solving this problem.
from collections import MutableMapping as _MutableMapping
