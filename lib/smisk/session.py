# encoding: utf-8
'''HTTP session store protocol.
'''

class Store:
  '''
  Session store interface definition.
  
  :type ttl:  int
  :type name: string
  '''
  
  ttl = 900
  name = 'SID'
  
  def read(self, session_id):
    '''
    Return the data associated with a session id.
    
    Called maximum once per *HTTP transaction*.
    
    If there is no session associated with ``session_id``, this method is
    responsible for and session initialization required by the underyling
    storage model.
    
    In the case where there is no data previously associated with the session
    id, this method should return None.
    
    :param  session_id: Session ID
    :type   session_id: string
    :rtype: object
    '''
    raise NotImplementedError
  
  def write(self, session_id, data):
    '''
    Associate data with a session id.
    
    Called at least once per *HTTP transaction* which has an active session.
    
    Normally, this will be called once, at the end of the *HTTP transaction*.
    This method should associate ``data`` with ``session_id``.
    
    :param  session_id:  Session ID
    :type   session_id:  string
    :param  data:        Data to be associated with ``session_id``
    :type   data:        object
    :rtype: None
    '''
    raise NotImplementedError
  
  def refresh(self, session_id):
    '''
    Refresh session.
    
    Called when a session is known to be in active use but has not been
    modified.
    
    For example, the built-in file-based session stores implementation
    uses ``touch session-file`` in order to refresh the sessions modified time,
    which is later used in the garbage collector-based model to detect dead
    sessions.
    
    :param  session_id:  Session ID
    :type   session_id:  string
    :rtype: None
    '''
    raise NotImplementedError
  
  def destroy(self, session_id):
    '''
    Destroy/delete/invalidate any session associated with ``session_id``.
    
    May be called any number of times during a *HTTP transaction*.
    
    :param  session_id: Session ID
    :type   session_id: string
    :rtype: None
    '''
    raise NotImplementedError
  

