ORM example
===========

This application demonstrates how to write a
`CRUD <http://en.wikipedia.org/wiki/Create,_read,_update_and_delete>`_ service,
in this case backed by a RDBM (relational database).

Fire up a server instance::

  $ cd examples/mvc/kittens-orm
  $ lighttpd -Df lighttpd.conf

Create a kitten::

  $ curl -id 'name=Leo&color=orange&year_born=2008' localhost:8080/create

Pet it::

  $ curl -i localhost:8080/read?name=Leo

Recolor it::

  $ curl -id 'name=Leo&color=purple' localhost:8080/update

Kill the poor little kitten::

  $ curl -id 'name=Leo' localhost:8080/delete

List all live kittens::

  $ curl -i localhost:8080/

You can also use a regular web browser since this demo include HTML templates
with *really* fancy input forms ;)
