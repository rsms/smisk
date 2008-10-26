#!/usr/bin/env python
# encoding: utf-8
def hello_app(env, start_response):
  start_response("200 OK", [('Content-type', 'text/plain')])
  response = ["Hello, World!\n\n"]
  response.append("Environment:\n\n")
  for k in sorted(env.keys()):
    response.append(" %s: %s\n" % (k, env[k]) )
  return response

# Start the application
from smisk.wsgi import main
main(hello_app)
