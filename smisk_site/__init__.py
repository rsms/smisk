#!/usr/bin/env python
# encoding: utf-8
import os, logging
from smisk.mvc import *

class root(Controller):
  site_menu = [
    dict(url='/',             title='Home', desc='Introduction to Smisk'),
    dict(url='/docs',         title='Docs', desc='Documentation and tutorials'),
    dict(url='/development',  title='Development', desc='Repository access, Bug management, etc'),
    dict(url='/download',     title='Download', desc='Build your first service in 5 minutes', id='download'),
  ]
  
  def __call__(self, *args, **kwargs):
    return { 'site_menu': self.site_menu }
  
  def docs(self, *args, **kwargs):
    return { 'site_menu': self.site_menu }


if __name__ == '__main__':
  Templates.errors = {404: 'errors/404'}
  app = Application(
    log_level=logging.DEBUG,
    autoreload=True
  )
  app.routes.map(r'^/docs/(?P<article>.+)', root().docs)
  main(app)
