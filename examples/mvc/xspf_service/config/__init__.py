# encoding: utf-8
app.autoreload = True

# Pretty-print XSPF by default
from smisk.serialization import xspf
xspf.Serializer.pretty_print = True

# Logging
logging.basicConfig(
  level=logging.DEBUG,
  format = '%(levelname)-8s %(name)-20s %(message)s',
  datefmt = '%d %b %H:%M:%S'
)
