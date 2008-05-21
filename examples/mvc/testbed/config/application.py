# encoding: utf-8

# If a template is added with the key 0 (zero), it will be used for any HTTP
# error which does _not_ have a explicit error template configured.
templates.errors = {
  404: 'errors/404.html'
}

# Routes
# The earlier it is specified, the higher the priority.
router.map(r'^/(favicon.ico$|res)', controller='files', action='send')
router.map('/', controller='posts', action='index')
router.map('/:controller/:action/:id')

# Database
model.metadata.bind = "mysql://hal_http_log:secret@hal.hunch.se/hal_http_log"
model.metadata.bind.echo = True

# Logging
logging.basicConfig(
  level = logging.DEBUG,
  stream = sys.stdout,
  #filename = os.path.join(appdir, 'log', 'application.log'),
  format = '%(asctime)s.%(msecs)d %(levelname)-8s %(name)-7s %(message)s',
  datefmt = '%d %b %H:%M:%S',
)
