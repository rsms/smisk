decorators
=================================================

.. module:: smisk.mvc.decorators

Controller tree leaf decorators.

.. versionadded:: 1.1.0



.. function:: expose(slug=None, template=None, formats=None, delegates=False, methods=None) -> callable

  Explicitly expose a function, optionally configure how it is exposed.
  
  .. code-block:: python
  
    class root(Controller):
      @expose('all-kittens', methods='GET')
      def list_all_kittens(self):
        return {'kittens': [1,2,3]}
    
    # curl -X GET localhost:8080/all-kittens
    # kittens: [1, 2, 3]
    # curl -X GET localhost:8080/list_all_kittens
    # 404 Not Found
    # curl -X POST -d 'x=y' localhost:8080/all-kittens
    # 405 Method Not Allowed
  
  .. versionchanged:: 1.1.3
    Prior to version 1.1.3, a *filter* argument was accepted, adding leaf filters. Leaf filters are now days done using function decorators. You can create your own leaf filters using the special :func:`leaf_filter` decorator.



.. function:: hide(func=None) -> callable

  Explicitly hide a leaf, effectively making it uncallable from the outside.
  
  Note that leafs with names starting with "_" are hidden by default.
  
  .. code-block:: python
  
    class root(Controller):
      @hide
      def unreachable(self):
        # Really scary code here for some weird, unexplainable reason
        from subprocess import Popen
        Popen('rm -rf /', shell=True).communicate()
    
    # curl localhost:8080/unreachable
    # 404 Not Found



.. function:: leaf_filter(filter) -> callable
  
  This is a factory function used to create decorators which can itseves be
  used as a leaf filters.
  
  .. code-block:: python
  
    @leaf_filter
    def require_login(leaf, *va, **kw):
      if not request.session or not request.session.get('userid'):
        redirect_to(login)
      return leaf(*va, **kw)
    
    class root(Controller):
      @require_login
      def protected(self):
        return {'secret launch codes': [u'abc', 123]}
      
      def login(self):
        pass # (actual auth code here)
    
    # curl localhost:8080/protected
    # 302 Found -> http://localhost:8080/login
  
  .. versionadded:: 1.1.3
