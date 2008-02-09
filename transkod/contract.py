#!/usr/bin/env python
# encoding: utf-8
"""
Copyright (c) 2007 Rasmus Andersson
"""

import sys, os, logging
from optparse import OptionParser
from transkod.pyext import Definition

__revision__ = '$Revision: 1$'.split(' ')[1][:-1]
log = logging.getLogger(__name__)

def main():
	optparser = OptionParser(version="%prog r"+str(__revision__), usage="usage: %prog [options] model")
	optparser.add_option("-v", "--verbosity", dest="verbosity",
	                  help="set verbosity level. (1-50) Lower value means more output.", metavar="LEVEL", default=20)
	(options, args) = optparser.parse_args()
	global log
	log = logging.getLogger(os.path.basename(sys.argv[0]))
	logging.basicConfig(level=options.verbosity, format='%(levelname)s %(message)s')
	
	if len(args) == 0:
		args = ['model.txt']
		#logging.error("Missing required argument 'model'")
		#return 1
	
	for filename in args:
		doc = None
		if filename == '-':
			log.info("Parsing H data from stdin")
			model = Definition(sys.stdin)
		else:
			log.info("Parsing H data from file %s", os.path.abspath(filename))
			model = Definition(open(filename, 'r'))
		print model
	
	return 0


if __name__ == '__main__':
	sys.exit(main())
