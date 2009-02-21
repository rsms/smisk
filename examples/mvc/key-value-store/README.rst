Key-Value store
===============

This example illustrates using the full power of HTTP and Smisk in the form of
a key-value store.

* Restricting HTTP methods on controller tree leafs.
* Mapping different methods to different leafs on the controller tree.

Different request methods do different things:

* GET requests reads entries
* PUT or POST requests writes entries
* DELETE requests removes entries
* OPTIONS requests gives API reflection

If you start the application and access it trough a web browser, there is an
ajax interface for manipulating the key-value store, passing data as JSON.
Parts of the javascript code within templates/__call__.html are universal and
can be used to interface with any Smisk service which have JSON capabilities.

Example
-------

Example of interfacing with this service using curl::

  $ curl -X GET localhost:8080/entry/my-key
  404 Not Found
  $ curl -X PUT -d value=hello localhost:8080/entry/my-key
  $ curl -X GET localhost:8080/entry/my-key.txt
  value: hello
  $ curl -X PUT \
    -H 'Content-Type: application/json' \
    -d '{"value":{"message": "hello internets", "time":123456}}' \
    localhost:8080/entry/something-else
  $ curl -X GET localhost:8080/entry/something-else.txt
  value: 
    message: hello internets
    time: 123456
  $ curl -X PUT -d '{"value":5}' localhost:8080/entry/something-else.json
  $ curl -X GET localhost:8080/entry/something-else.txt
  value: 5
  $ curl -X POST -d 'value=internets' localhost:8080/entry/something-else
  $ curl -X GET localhost:8080/entry/something-else.txt
  value: internets
  $ curl -X DELETE localhost:8080/entry/something-else
  $ curl -X GET localhost:8080/entry/something-else.txt
  404 Not Found


Tip
^^^

If you are using bash as your shell (which you probably are if you don't know what that is), you can create 100 keys to play with using this line::

  for (( i=0; i<=100; i++ )); do curl -X PUT -d 'value=hello'$i 'localhost:8080/entry/my-key'$i; done
