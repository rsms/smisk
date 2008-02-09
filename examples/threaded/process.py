#!/usr/bin/env python
# encoding: utf-8
import sys, os, fcgi, time

# Determines how often the interpreter checks for periodic things such as
# thread switches and signal handlers. Setting it to a larger value may
# increase performance for programs using threads. Default: 100.
#sys.setcheckinterval(1000)

def doit(thread_id):
	def log(s):
		sys.stderr.write("%s: %s\n" % (log.prefix, s))
	log.prefix = "%s thread %d" % (os.path.basename(sys.argv[0]), thread_id)
	request = fcgi.Request()
	log("listening")
	while request.accept():
		if 'CONTENT_LENGTH' in request.params:
			content_length = int(request.params['CONTENT_LENGTH'])
			if content_length:
				request.input.read(content_length)
		#		while 1:
		#			line = request.input.readline()
		#			if line is None:
		#				break
		#			log("input line: %s" % repr(line))
		bytes = request.out.write("Content-type: text/plain\r\nContent-length: 12\r\n\r\nH3llo W0rld\n")
		#log("wrote %d bytes to request.out" % bytes)
	log("exiting")

def main():
	thread_count = 8
	if 'THREADS' in os.environ:
		thread_count = int(os.environ['THREADS'])
	if thread_count:
		from threading import Thread
		threads = []
		for thread_id in xrange(thread_count):
			t = Thread(target=doit, args=tuple([thread_id+1]))
			t.start()
			threads.append(t)
		
		# Okay, so Python does not have the ability to interrupt threads.
		# we use time.sleep, since it is interruptable and uses a mutex.
		try:
			while 1: time.sleep(99999999)
		except:
			pass
		
		try:
			fcgi.shutdown()
			for t in threads:
				t.join(2)
		finally:
			sys.exit(0)
	else:
		doit(0)



main()
