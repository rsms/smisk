# encoding: utf-8
'''Leaf filters
'''
import smisk.core

__all__ = ['confirm']

def confirm(leaf, *va, **params):
  '''Requires the client to resend the request, passing a one-time
  valid token as confirmation.
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
  
