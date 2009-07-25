# encoding: utf-8
'''Leaf filters
'''
import smisk.core
import smisk.mvc.http as http
from smisk.mvc.decorators import leaf_filter
from time import time
try:
	from hashlib import md5
except ImportError:
	from md5 import md5

__all__ = ['confirm']


@leaf_filter
def confirm(leaf, *va, **params):
  '''Requires the client to resend the request, passing a one-time
  valid token as confirmation.
  '''
  req = smisk.core.Application.current.request

  # Validate confirmation if available
  params['confirmed'] = False
  try:
    if params['confirm_token'] == req.session['confirm_token']:
      params['confirmed'] = True
  except (KeyError, TypeError):
    pass
  
  # Make sure we don't keep confirm_token in params
  try: del params['confirm_token']
  except: pass
  
  # Call leaf
  rsp = leaf(*va, **params)

  # Add confirmation token if still unconfirmed
  if not params['confirmed']:
    if not isinstance(req.session, dict):
      req.session = {}
    confirm_token = smisk.core.uid()
    req.session['confirm_token'] = confirm_token
    if not isinstance(rsp, dict):
      rsp = {}
    rsp['confirm_token'] = confirm_token
  else:
    # Remove confirmation tokens
    try: del req.session['confirm_token']
    except: pass
    try: del rsp['confirm_token']
    except: pass

  # Return response
  return rsp


class DigestAuthFilter(object):
	'''HTTP Digest authorization filter.
	'''
	required = ['username', 'realm', 'nonce', 'uri', 'response']
	users = {}
	
	def __init__(self, realm, users=None, require_authentication=True):
		self.realm = realm
		if users is not None:
			self.users = users
		self.require_authentication = require_authentication
		self.leaf = None
		self.app = smisk.core.Application.current
	
	def respond_unauthorized(self, send401=True, *va, **kw):
		if not send401:
			kw['authorized_user'] = None
			return self.leaf(*va, **kw)
		# send response
		self.app.response.headers.append(
			'WWW-Authenticate: Digest realm="%s", nonce="%s", algorithm="MD5", qop="auth"'
				% (self.realm, self.create_nonce())
		)
		raise http.Unauthorized()
	
	def respond_authorized(self, user, *va, **kw):
		kw['authorized_user'] = user
		return self.leaf(*va, **kw)
	
	def get_authorized(self, username):
		# subclasses can return an alternative object which will be propagated 
		return username
	
	def create_nonce(self):
		return md5('%d:%s' % (time(), self.realm)).hexdigest()
	
	def H(self, data):
		return md5(data).hexdigest()
	
	def KD(self, secret, data):
		return self.H(secret + ':' + data)
	
	def filter(self, *va, **kw):
		# did the client even try to authenticate?
		if 'HTTP_AUTHORIZATION' not in self.app.request.env:
			return self.respond_unauthorized(self.require_authentication, *va, **kw)
		
		# not digest auth?
		if not self.app.request.env['HTTP_AUTHORIZATION'].startswith('Digest '):
			raise http.BadRequest('only Digest authorization is allowed')
		
		# parse
		params = {}
		required = len(self.required)
		for k, v in [i.split("=", 1) for i in self.app.request.env['HTTP_AUTHORIZATION'][7:].strip().split(',')]:
			k = k.strip()
			params[k] = v.strip().replace('"', '')
			if k in self.required:
				required -= 1
		
		# missing required parameters?
		if required > 0:
			raise http.BadRequest('insufficient authorization parameters')
		
		# user exists?
		if params['username'] not in self.users:
			return self.respond_unauthorized(True, *va, **kw)
		
		# build A1 and A2
		A1 = '%s:%s:%s' % (params['username'], self.realm, self.users[params['username']])
		A2 = self.app.request.method + ':' + self.app.request.url.uri
		
		# build expected response
		expected_response = None
		if 'qop' in params:
			# if qop is sent then cnonce and nc MUST be present
			if not 'cnonce' in params or not 'nc' in params:
				raise http.BadRequest('cnonce and/or nc authorization parameters missing')
			
			# only auth type is supported
			if params['qop'] != 'auth':
				raise http.BadRequest('unsupported qop ' + params['qop'])
			
			# build
			expected_response = self.KD(self.H(A1), '%s:%s:%s:%s:%s' % (
				params['nonce'], params['nc'], params['cnonce'], params['qop'], self.H(A2)))
		else:
			# qop not present (compatibility with RFC 2069)
			expected_response = self.KD(self.H(A1), params['nonce'] + ':' + self.H(A2))
		
		# 401 on realm mismatch
		if params['realm'] != self.realm:
			log.debug('auth failure: unexpected realm')
			return self.respond_unauthorized(True, *va, **kw)
		
		# 401 on unexpected response
		if params['response'] != expected_response:
			log.debug('auth failure: unexpected digest response')
			return self.respond_unauthorized(True, *va, **kw)
		
		# authorized -- delegate further down the filter chain
		return self.respond_authorized(params['username'], *va, **kw)
	
	def __call__(self, leaf):
		self.leaf = leaf
		def f(*va, **kw):
			return self.filter(*va, **kw)
		f.parent_leaf = leaf
		f.__name__ = leaf.__name__+'_with_DigestAuthFilter'
		return f
	
