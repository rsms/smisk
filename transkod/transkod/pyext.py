#!/usr/bin/env python
# encoding: utf-8
"""
Copyright (c) 2007 Rasmus Andersson
"""

import logging
from dom import Document, Element

__revision__ = '$Revision: 1$'.split(' ')[1][:-1]
log = logging.getLogger(__name__)

class ModuleElement(Element): pass
class ClassElement(Element): pass

class TypeElement(Element):
	default_type = "void"
	def __init__(self, *args):
		args = list(args)
		if len(args) > 1:
			self.type = args[0]
			args[0] = args[1]
			del args[1]
		else:
			self.type = self.default_type
		super(TypeElement, self).__init__(*args)

class FunctionElement(TypeElement): pass
class VarElement(TypeElement): pass
class InstanceVarElement(VarElement): pass
class ClassVarElement(VarElement): pass

class Definition(Document):
	types = {
		'module':ModuleElement,
		'class':ClassElement,
		'func':FunctionElement,
		'var':VarElement,
		'ivar':InstanceVarElement,
		'cvar':ClassVarElement
	}
