# encoding: utf-8
'''Leaf filters
'''
import smisk.core

__all__ = ['confirm']

def confirm(leaf, *va, **params):
  '''Requires the client to resend the request, passing a one-time valid token
  as a confirmation.
  
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
  "confirm_token" and adds the same string to the response, keyed by 
  "confirm_token". The client needs to send the same request again
  with the addition of passing "confirm_token", as a confirmation. This
  token will only be valid for one confirmation, thus providing a good
  protection against accidents.
  
  The leaf being filtered by these filters receives a boolean kewyword
  argument named "confirmed":
  
   * When the value of this argument is True, the client did confirm (client
     sent a request containing a valid token). In this case, you should perform
     whatever leaf needed to be confirmed.
     
   * When the value of "confirmed" is False, the client has not confirmed or
     tried to confirm with an invalid token. In this case, you should respond
     with some kind of information, telling the client to send a new request
     with the attached token.
  
  Note: This filter will force the session to be a dictionary. If session is 
  something else, this filter will replace session::
  
    if not isinstance(req.session, dict):
      req.session = {}
  
  '''
  def f(*va, **params):
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
  
  return f
  
