# encoding: utf-8
Templates.errors = {403: 'errors/404'}
app.routes.filter(r'^/docs/(?P<article>.+)', '/docs')

logging.basicConfig(
  level=logging.DEBUG,
  format = '%(levelname)-8s %(name)-20s %(message)s',
  datefmt = '%d %b %H:%M:%S'
)