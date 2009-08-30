# encoding: utf-8
'''Leaf filters
'''
import smisk.core
import smisk.mvc.http as http
from smisk.core import Application as App
from smisk.mvc.decorators import leaf_filter, LeafFilter
from smisk.mvc.helpers import redirect_to
from smisk.mvc.model import sql
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
	req = App.current.request
	
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


class AuthFilter(LeafFilter):
	authorized_param = 'authorized_user'
	create_leaf = None
	
	def __init__(self, create_leaf=None, authorized_param=None):
		if create_leaf:
			self.create_leaf = create_leaf
		if authorized_param:
			self.authorized_param = authorized_param
	
	@property
	def authorized(self):
		raise NotImplementedError('authorized')
	
	@property
	def have_valid_create_leaf(self):
		return self.create_leaf and (isinstance(self.create_leaf, basestring) or control.uri_for(self.create_leaf) is not None)
	
	def will_authorize(self, *va, **kw):
		pass
	
	def did_authorize(self, user, rsp, exc):
		pass
	
	def did_fail(self):
		if not self.have_valid_create_leaf:
			raise http.Unauthorized()
		redirect_to(self.create_leaf)
	
	def create(self, leaf):
		return self.filter_proxy(leaf, self._create)
	
	def _create(self, leaf, *va, **kw):
		exc = None
		rsp = None
		self.will_authorize(va, kw)
		try:
			rsp = leaf(*va, **kw)
		except http.HTTPExc, e:
			exc = e
		if rsp and isinstance(rsp, dict) and self.authorized_param in rsp and rsp[self.authorized_param]:
			self.did_authorize(rsp[self.authorized_param], rsp, exc)
		if exc:
			raise exc
		return rsp
	
	def require(self, leaf):
		return self.filter_proxy(leaf, self._require)
	
	__call__ = require
	
	def _require(self, leaf, *va, **kw):
		if not self.authorized:
			self.did_fail()
		return leaf(*va, **kw)
	
	def destroy(self, leaf):
		return self.filter_proxy(leaf, self._destroy)
	
	def _destroy(self, leaf, *va, **kw):
		App.current.request.session = None
		return leaf(*va, **kw)
	

class SessionAuthFilter(AuthFilter):
	referrer_param = 'auth_referrer'
	
	@property
	def session(self):
		if not isinstance(App.current.request.session, dict):
			App.current.request.session = {}
		return App.current.request.session
	
	@property
	def authorized(self):
		if isinstance(App.current.request.session, dict):
			return App.current.request.session.get(self.authorized_param)
	
	def will_authorize(self, va, kw):
		if self.referrer_param in kw:
			self.session[self.referrer_param] = kw[self.referrer_param]
			del kw[self.referrer_param]
	
	def did_authorize(self, user, rsp, exc):
		self.session[self.authorized_param] = user
		if self.referrer_param in self.session:
			referrer = self.session[self.referrer_param]
			del self.session[self.referrer_param]
			redirect_to(referrer)
	
	def did_fail(self):
		if not self.have_valid_create_leaf:
			raise http.Unauthorized()
		redirect_to(self.create_leaf, **{self.referrer_param: App.current.request.url})
	

class DigestAuthFilter(LeafFilter):
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
	
	def respond_unauthorized(self, send401=True, *va, **kw):
		if not send401:
			kw['authorized_user'] = None
			return self.leaf(*va, **kw)
		# send response
		App.current.response.headers.append(
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
		if 'HTTP_AUTHORIZATION' not in App.current.request.env:
			return self.respond_unauthorized(self.require_authentication, *va, **kw)
		
		# not digest auth?
		if not App.current.request.env['HTTP_AUTHORIZATION'].startswith('Digest '):
			raise http.BadRequest('only Digest authorization is allowed')
		
		# parse
		params = {}
		required = len(self.required)
		for k, v in [i.split("=", 1) for i in App.current.request.env['HTTP_AUTHORIZATION'][7:].strip().split(',')]:
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
		A2 = App.current.request.method + ':' + App.current.request.url.uri
		
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
	

class sortable_entities(LeafFilter):
	'''Sort sets of Elixir entities
	
	Usage:
	
		@sortable_entities(UserAccount, 'users', 'created')
		def users(self):
			return {'users': UserAccount.query}
	
	'''
	def __init__(self, entity, parameter, sortdefault, orderdefault='desc', kwprefix=''):
		self.entity = entity
		self.parameter = parameter
		self.sortdefault = sortdefault
		self.orderdefault = orderdefault
		self.kwprefix = kwprefix
	
	def filter(self, leaf, *va, **kw):
		rsp = leaf(*va, **kw)
		if self.parameter in rsp:
			q = rsp[self.parameter]
		else:
			q = self.entity.query
		if not q:
			return rsp
		sort = kw.get(self.kwprefix+'sort', self.sortdefault)
		order = kw.get(self.kwprefix+'order', self.orderdefault)
		if sort:
			sort_key = getattr(self.entity, sort)
			if order == 'desc':
				q = q.order_by(sql.desc(sort_key))
			else:
				q = q.order_by(sort_key)
		rsp.update({
			self.parameter: q.all(),
			self.kwprefix+'sort': sort,
			self.kwprefix+'order': order,
			self.kwprefix+'inverse_order': ('desc','asc')[int(order=='desc')]
		})
		return rsp
	
