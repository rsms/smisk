#!/usr/bin/env python
# encoding: utf-8
"""
Copyright (c) 2007 Rasmus Andersson
"""

import sys, os, logging
from cStringIO import StringIO

__revision__ = '$Revision: 1$'.split(' ')[1][:-1]
log = logging.getLogger(__name__)


class Element(object):
	def __init__(self, *args):
		if len(args):
			self.name = args[0]
			self.attributes = args[1:]
		else:
			self.name = None
			self.attributes = []
		self.children = []
		self.parent = None
	
	def dump(self, intend=0):
		v = []
		for e in self.children:
			v.append(e.dump(intend+1))
		s = "  "*intend + "%s" % repr(self)
		if len(v):
			v[0:0] = ['']
			s += "\n".join(v)
		return s
	
	def _dump_children(self):
		v = []
		for e in self.children:
			v.append(e._dump_children())
		return "\n".join(v)
	
	def __repr__(self):
		s = ""
		if self.attributes is not None and len(self.attributes):
			s = " " + repr(self.attributes)
			if len(s) > 1 and s[-2:-1] == ',':
				s = s[:-2]+')'
		return "<%s %s%s>" % (self.__class__.__name__, repr(self.name), s)
	

class Document(object):
	"""docstring for Document"""
	
	types = {}
	
	def __init__(self, file=None, string=None):
		self.root = None
		if file is not None or string is not None:
			if file is None:
				file = StringIO(string)
			try:
				self._parse(file)
			finally:
				file.close()
	
	def __str__(self):
		return self.root.dump()
	
	def loadString(self):
		"""docstring for loadString"""
		pass
	
	def _parse(self, file):
		lineno = 0
		previndent = 0
		self.root = Element("root")
		stack = [[self.root],[],[],[]]
		
		for line in file:
			llen = len(line)
			lineno += 1
			indent = 1
			e = None
			
			log.debug(" # %d ---------------", lineno)
			
			for c in line:
				if c != ' ' and c != "\t":
					break
				indent += 1
			
			if indent-1 > previndent:
				log.warning("intentation deeper than expected at line %d", lineno)
				indent -= 1
			
			log.debug(" L %d", indent)
			
			line = line.strip()
			if not len(line):
				continue
			
			lv = line.replace("\t"," ").split(" ")
			lvlen = len(lv)
			etype = lv[0].lower()
			
			if etype in self.types.keys():
				del lv[0]
				e = self.types[etype](*lv)
			else:
				log.info("generic item %s at line %d", repr(line), lineno)
				e = Element(line, *lv)
			
			
			if indent < previndent:
				self._flush_stack(previndent, indent, stack)
			
			log.debug("   indent: %d, previndent: %d", indent, previndent)
			#log.info("   stack: %s")
			if len(stack)-1 < indent:
				for i in xrange(indent-len(stack)+1):
					stack.append([])
			stack[indent].append(e)
			#log.info("   stack: %s", str(stack))
			
			previndent = indent
		
		self._flush_stack(previndent, 0, stack)
	
	def _flush_stack(self, previndent, indent, stack):
		#log.debug("<- previndent-indent=%d", previndent-indent)
		parentelem = None
		for i in xrange(previndent-indent):
			#log.debug("   i: %d  previndent: %d  stack[%d]: %s", i, previndent, previndent-i-1, repr(stack[previndent-i-1]))
			for x in xrange(previndent):
				if len(stack[previndent-i-1-x]):
					parentelem = stack[previndent-i-1-x][-1]
					break
			#log.debug("parentelem: %s", parentelem);
			for elem in stack[previndent-i]:
				elem.parent = parentelem
			#log.debug("moved stack[%d] to %s.children", previndent-i, parentelem);
			parentelem.children = stack[previndent-i]
			stack[previndent-i] = []
		#log.info("   stack: %s", str(stack))
		#log.info(":: %s", parentelem.dump())
	

