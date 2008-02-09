#!/usr/bin/env python
# encoding: utf-8
import sys, os, fcgi, time, signal
from threading import Thread, Lock

# Determines how often the interpreter checks for periodic things such as
# thread switches and signal handlers. Setting it to a larger value may
# increase performance for programs using threads. Default: 100.
#sys.setcheckinterval(1000)

def log(tid, s):
	sys.stderr.write(log.format % (tid, s))
log.format = "%s%%s: %%s\n" % os.path.basename(sys.argv[0])

def doit(thread_id):
	tid = " thread %d" % thread_id
	request = fcgi.Request()
	log(tid, "listening")
	while request.accept():
		request.out.write("Content-type: text/plain\r\nContent-length: 12\r\n\r\nH3llo W0rld\n")
	log(tid, "exiting")

def intHandler(signum, frame):
	fcgi.shutdown()
	time.sleep(3)
	sys.exit(0)

def main():
	# setup signal handlers
	#signal.signal(signal.SIGINT, intHandler)
	signal.signal(signal.SIGTERM, intHandler)
	
	thread_count = 2
	threads = []
	
	fcgi.bind(":5000")
	
	for thread_id in xrange(thread_count):
		t = Thread(target=doit, args=tuple([thread_id+1]))
		t.start()
		threads.append(t)
	
	try:
		while 1: time.sleep(99999999)
	except:
		pass
	
	log(" main", "graceful shutdown initiated")
	try:
		fcgi.shutdown()
		for t in threads:
			t.join(2)
	finally:
		sys.exit(0)

main()
