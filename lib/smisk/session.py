# encoding: utf-8

class Store:
  '''
  Session store interface definition.
  
  Any session store must implement this interface.
  
  `Application` keeps alot of session "settings", like TTL (or "max lifetime").
  You can always get a hold of the current `Application` by calling the static
  method `Application.current()`. For example, you can aquire the TTL value
  like this: ``Application.current().session_ttl``.
  
  :ivar uses_gc: If the Store uses Garbage Collection to handle old sessions,
                this should have a True value and the Store must implement the
                `gc()` method.
  :type uses_gc: bool
  '''
  
  uses_gc = True
  
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
    which is later used in `smisk.core.FileSessionStore.gc()` to detect dead
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
  
  def gc(self, max_lifetime):
    '''
    Periodically called to allow for deletion of timed out sessions.
    
    Should delete any session data which is older than ``max_lifetime``
    seconds.
    
    This method is only required and used if the `uses_gc` instance variable
    evaluates to True.
    
    There is no way to know exactly when this method will be called, since
    it uses a probabilistic approach to decide when it's time to garbage
    collect. It will be ran just after some *HTTP transaction* has finished,
    and is guaranteed not to be ran at the same time as any of `read()`,
    `write()`, `refresh()` or `destroy()`.
    
    :param  max_lifetime: Maximum lifetime expressed in seconds
    :type   max_lifetime: int
    :rtype: None
    '''
    raise NotImplementedError

