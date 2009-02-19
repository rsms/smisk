Custom serialization
====================

This simple example demonstrates how to create custom data serializers.

In this example, we have created a custom XML serializer which builds upon the
xmlbase Element Tree backed base serializer, minimizing code. We have also
created a very simple text serializer without building upon any readymade code.


Trying it out
-------------

Start a server::

  $ cd examples/mvc/custom-serialization
  $ lighttpd -Df lighttpd.conf

In another terminal, run a client::

  $ curl -i localhost:8080/.mytext

This will give you some sample data serialized with my_text_serializer. Let's
try to have the sample data (built-in -- see app.py) returned as xml, using our
my_xml_serializer::

  $ curl -i localhost:8080/.xml

It's that simple!

In app.py we have defined another method which echoes back whatever parameters 
was sent to it. Let's convert some JSON-formatted data into our custom XML
format::

  $ curl -i \
    -d '{"name":"Bulgur R.", "age":42}' \
    -H 'Content-Type: application/json' \
    localhost:8080/echo.xml

Or we could specify our capabilities and have Smisk choose the best representation::

  $ curl -i \
    -d '{"name":"Bulgur R.", "age":42}' \
    -H 'Content-Type: application/json' \
    -H 'Accept: text/x-mytext, text/xml;q=0.5' \
    localhost:8080/echo

Let's also specify what kind of character encoding we accept. Smisk will chose
the most appropriate character set, honoring our my_text_serializer's
"prefered character encoding"::

  $ curl -i \
    -d '{"name":"Bulgur R.", "age":42}' \
    -H 'Content-Type: application/json' \
    -H 'Accept: text/x-mytext, text/xml;q=0.5' \
    -H 'Accept-Charset: iso-8859-1, utf-8, ascii;q=0.5' \
    localhost:8080/echo

And we got the data returned, formatted using our my_text_serializer and characters
encoded as utf-8 (because our serializer prefers it that way and the client accepts
it without any quality limitations).
