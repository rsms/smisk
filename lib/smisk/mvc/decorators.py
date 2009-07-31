# encoding: utf-8
'''Controller tree function decorators.
'''
import types

__all__ = ['expose', 'hide', 'leaf_filter']

def expose(slug=None, template=None, formats=None, delegates=False, methods=None):
	'''Explicitly expose a function, optionally configure how it is exposed.
	'''
	def entangle(func):
		# Note: We do not add default values (i.e. methods = None) because we can not gurantee
		#			 that every leaf called has been @expose'd, so we need to check for attribute
		#			 existance anyway outside of this scope.
		
		# Slug
		if slug is not None:
			# Slug might be the function if decorator called without ()
			if isinstance(slug, basestring):
				func.slug = unicode(slug)
			elif isinstance(slug, unicode):
				func.slug = slug
		
		# Delegates to other leafs up the class hierarchy?
		if delegates is not None:
			func.delegates = bool(delegates)
		
		# Template
		if template is not None:
			func.template = unicode(template)
		
		# Formats
		if formats is not None:
			if isinstance(formats, (list, tuple)):
				func.formats = formats
			else:
				func.formats = (formats,)
			for s in func.formats:
				if not isinstance(s, basestring):
					raise TypeError('formats must be a tuple or list of strings, alternatively a single string')
		
		# Methods
		if methods is not None:
			if isinstance(methods, (list, tuple)):
				func.methods = methods
			else:
				func.methods = (methods,)
			for s in func.methods:
				if not isinstance(s, basestring):
					raise TypeError('methods must be a tuple or list of strings, alternatively a single string')
			func.methods = [s.upper() for s in func.methods]
		
		return func
	
	if isinstance(slug, (types.FunctionType, types.MethodType)):
		return entangle(slug)
	return entangle


def hide(func=None):
	def entangle(func):
		func.hidden = True
		return func
	if isinstance(func, (types.FunctionType, types.MethodType)):
		return entangle(func)
	return entangle


def leaf_filter(filter):
	def entangle(leaf, *va, **kw):
		def f(*va, **kw):
			return filter(leaf, *va, **kw)
		f.parent_leaf = leaf
		return f
	entangle.__name__ = filter.__name__+'_leaf_filter'
	return entangle

class LeafFilter(object):
	'''Leaf filter factory baseclass
	
	Used like this:
	
		myf = MySubclass()
		...
		@myf
		def some_leaf...
	
	'''
	def filter_proxy(self, leaf, filter):
		def f(*va, **kw):
			return filter(leaf, *va, **kw)
		f.parent_leaf = leaf
		f.__name__ = leaf.__name__+'_with_'+self.__class__.__name__+'_'+filter.__name__
		return f
	
	def __call__(self, leaf):
		return self.filter_proxy(leaf, self.filter)
	
	def filter(self):
		raise NotImplementedError('filter')
	

	
