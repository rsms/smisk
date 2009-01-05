# encoding: utf-8
'''Leaf filters
'''
import smisk.core

__all__ = ['BaseFilter', 'confirm']

class BaseFilter(object):
  '''Base filter with a pass-through implementation.
  '''
  @staticmethod
  def before(cls, *args, **kw):
    '''Called before mvc.Application.service calls the actual leaf.
    
    Should return a tuple of (args, kw)
    '''
    return args, kw
  
  @staticmethod
  def after(cls, rsp, *args, **kw):
    '''Called after mvc.Application.service has called the actual leaf.
    
    rsp is the object returned from the actual leaf.
    
    Should return rsp
    '''
    return rsp
  

class confirm(BaseFilter):
  '''Requires the client to resend the request, passing a one-time valid token
  as a confirmation.
  
  Used like this::
  
    @expose(filters=filters.confirm)
    def delete(self, id, confirmed=False, *args, **kwargs):
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
  @staticmethod
  def before(confirm_token=None, *args, **kw):
    kw['confirm_token'] = confirm_token
    kw['confirmed'] = False
    try:
      if confirm_token == smisk.core.Application.current.request.session['confirm_token']:
        kw['confirmed'] = True
    except (KeyError, TypeError):
      pass
    return args, kw
  
  @staticmethod
  def after(rsp, confirmed=False, *args, **kw):
    if not confirmed:
      req = smisk.core.Application.current.request
      if not isinstance(req.session, dict):
        req.session = {}
      confirm_token = smisk.core.uid()
      req.session['confirm_token'] = confirm_token
      #log.info("session['confirm_token']=%r", req.session['confirm_token'])
      if not isinstance(rsp, dict):
        rsp = {}
      rsp['confirm_token'] = confirm_token
    return rsp
  
