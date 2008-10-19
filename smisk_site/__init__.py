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
  
  @expose
  def __call__(self, *args, **params):
    def fmt(ln):
      try: return '/'.join(ln)
      except TypeError: return None
    for node in [root, root.docs, xyz, xyz.secret, xyz.show_people, internet.power]:
      log.info('path_to:      %-35r => %r', node, fmt(control.path_to(node)) )
      log.info('template_for: %-35r => %r', node, fmt(control.template_for(node)) )
    return { 'site_menu': self.site_menu }
  
  @expose(template='documentation')
  def docs(self, *args, **params):
    return { 'site_menu': self.site_menu }
  
  def echo(self, *args, **params):
    return dict(args=args, params=params)
  

class xyz(root):
  slug = 'x-y-z'
  
  def __call__(self, *args, **params):
    pass
  
  @hide
  def secret(self, *args, **params):
    pass
  
  @expose('show-people')
  def show_people(self, *args, **params):
    return {'people': 'are crazy'}


class internet(xyz):
  slug = None
  
  @expose(template='_footer')
  def power(self, *args, **params):
    pass
  

if __name__ == '__main__':
  main()
