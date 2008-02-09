#!/usr/bin/env python
# encoding: utf-8
import sys, fcgi

try:
	request = fcgi.Request()
	while request.accept():
		request.sendfile(request.params['SCRIPT_FILENAME'])
except KeyboardInterrupt:
	pass
