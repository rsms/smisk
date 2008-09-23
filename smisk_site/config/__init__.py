# encoding: utf-8
Templates.errors = {404: 'errors/404'}
app.autoreload = True
app.routes.filter(r'^/docs/(?P<article>.+)', '/docs')

logging.basicConfig(
  level=logging.DEBUG,
  format = '%(levelname)-8s %(name)-20s %(message)s',
  datefmt = '%d %b %H:%M:%S'
)