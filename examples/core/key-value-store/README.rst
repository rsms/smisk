RESTful key-value store
=======================

Backed by smisk.ipc.shared_dict.
Speaks JSON.

There is also a much more feature-rich and production-like application doing the
exact same thing, but built using smisk.mvc in examples/mvc/key-value-store.

Example using curl::

  $ curl http://localhost:8080/
  {"keys": []}
  $ curl http://localhost:8080/my-key
  {"status": "No such key 'my-key'"}
  $ curl -X PUT -d '"my value"' http://localhost:8080/my-key
  {"status": "OK"}
  $ curl http://localhost:8080/my-key
  "my value"
  $ curl http://localhost:8080/
  {"keys": ["my-key"]}
  $ curl -X DELETE http://localhost:8080/my-key
  {"status": "OK"}
  $ curl http://localhost:8080/my-key
  {"status": "No such key 'my-key'"}
  $ curl http://localhost:8080/
  {"keys": []}

