#!/usr/bin/env python
# encoding: utf-8
import smisk, sys
from smisk.wsgi import Gateway

# A simple WSGI handler
def hello_app(env, start_response):
  start_response("200 OK", [('Content-type', 'text/plain')])
  response = ["Hello, World!\n\n"]
  response.append("Environment:\n\n")
  for k in sorted(env.keys()):
    response.append(" %s: %s\n" % (k, env[k]) )
  return response

# If any arguments was passed to us, we bind as a stand-alone process:
if len(sys.argv) > 1:
  smisk.bind(sys.argv[1])
  print "Listening on %s" % sys.argv[1]

# Start the application
Gateway(hello_app).run()
