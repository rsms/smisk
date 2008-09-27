# encoding: utf-8
app.autoreload = True
app.show_traceback = True

# Pretty-print XSPF by default
from smisk.codec import xspf
xspf.codec.pretty_print = True

# Logging
logging.basicConfig(
  level=logging.INFO,
  format = '%(levelname)-8s %(name)-20s %(message)s',
  datefmt = '%d %b %H:%M:%S'
)
