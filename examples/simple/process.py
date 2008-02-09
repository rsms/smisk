#!/usr/bin/env python
# encoding: utf-8
import sys, fcgi

try:
	request = fcgi.Request()
	while request.accept():
		request.out.write("Content-type: text/plain\r\nContent-length: 12\r\n\r\nHello World\n")
except KeyboardInterrupt:
	pass
