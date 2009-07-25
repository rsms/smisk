filters
=================================================

.. module:: smisk.mvc.filters
.. versionadded:: 1.1.0


.. function:: confirm(leaf, *va, **params)
	
	Requires the client to resend the request, passing a one-time valid token
	as confirmation.
	
	Used like this::
	
		@confirm
		def delete(self, id, confirmed, *args, **kwargs):
			item = Item.get_by(id=id)
			if confirmed:
				item.delete()
				return {'msg': 'Item was successfully deleted'}
			else:
				return {'msg': 'To confirm deletion, make a new request and '\
				               'include the attached confirm_token'}
	
	Generates a random string which is stored in session with the key
	``confirm_token`` and adds the same string to the response, keyed by 
	``confirm_token``. The client needs to send the same request again
	with the addition of passing "confirm_token", as a confirmation. This
	token will only be valid for one confirmation, thus providing a good
	protection against accidents.
	
	The leaf being filtered by these filters receives a boolean keyword
	argument named ``confirmed``:
	
	 * When the value of this argument is True, the client did confirm (client
		 sent a request containing a valid token). In this case, you should perform
		 whatever leaf needed to be confirmed.
		 
	 * When the value of ``confirmed`` is false, the client has not confirmed or
		 tried to confirm with an invalid token. In this case, you should respond
		 with some kind of information, telling the client to send a new request
		 with the attached token.
	
	**Note:** This filter will force the session to be a dictionary. If session is 
	something else, this filter will replace session::
	
		if not isinstance(req.session, dict):
			req.session = {}
	
	

.. class:: DigestAuthFilter(object)
	
	HTTP Digest authorization filter.
	
	Used like this::
	
		authenticate = DigestAuthFilter('Protected', {'username': 'password'})
		check_authenticated = DigestAuthFilter('Protected', {'username': 'password'}, False)
		
		class root(Controller):
			@authenticate
			def only_for_users(self, authorized_user):
				# do something...
			
			@check_authenticated
			def for_everyone(self, authorized_user):
				if authorized_user:
					# do something only authorized users can do
				else:
					# do something unauthorized users can do
	
	.. versionadded:: 1.1.7
