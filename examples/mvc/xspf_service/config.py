# encoding: utf-8
app.autoreload = True
app.show_traceback = True

Application.default_format = 'xspf'

logging.basicConfig(
  format='%(levelname)-8s %(name)-20s %(message)s',
  level=logging.INFO
)
