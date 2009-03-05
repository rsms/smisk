#!/usr/bin/env python
# encoding: utf-8
import smisk.core.xml as xml
from smisk.util.benchmark import benchmark
#
# Recorded performance:
# 
# 2009-03-05, Rasmus Andersson
# On iMac 24, Intel Core 2 duo 2.8GHz (using one full core):
#
# FUNCTION  TYPE    PERFORMANCE
# --------- ------- -----------
# escape    bytes    122.7 MB/s
# escape    unicode   60.0 MB/s
# unescape  bytes    104.6 MB/s
# unescape  unicode   49.8 MB/s
#

DOCUMENT_BYTES = 'Some <document> with strings & characters which should be "escaped"' * 1024
DOCUMENT_UNICODE = u'Some <document> with strings & characters which should be "escaped"' * 1024

if __name__ == "__main__":
  
  iterations = 10000
  print 'test data is %d characters long' % len(DOCUMENT_BYTES)
  
  for x in benchmark('escape bytes', iterations):
    xml.escape(DOCUMENT_BYTES)
  
  for x in benchmark('escape unicode', iterations):
    xml.escape(DOCUMENT_UNICODE)
  
  escaped_bytes = xml.escape(DOCUMENT_BYTES)
  escaped_unicode = xml.escape(DOCUMENT_UNICODE)
  
  for x in benchmark('unescape bytes', iterations):
    xml.escape(escaped_bytes)
  
  for x in benchmark('unescape unicode', iterations):
    xml.escape(escaped_unicode)
