#!/usr/bin/env python
# encoding: utf-8
from smisk.mvc import *
from smisk.mvc.model import *
from smisk.serialization import xmlgeneric
import logging

log = logging.getLogger(__name__)

class Kitten(Entity):
  name = Field(Unicode(255), primary_key=True)
  color = Field(Unicode(30), required=True, default=u'purple')
  year_born = Field(Integer, required=True, default=0)

class root(Controller):
  def __call__(self, *args, **params):
    log.info('listing all kittens')
    return {'kittens': Kitten.query.all()}
  
  def create(self, name, color=None, year_born=None):
    name = name.strip()
    if not name:
      raise http.BadRequest('name attribute must not be empty')
    kitten = Kitten(name=name, color=color, year_born=year_born)
    log.info('created kitten: %r', kitten)
    redirect_to(self.read, kitten)
  
  def read(self, name):
    log.info('reading kitten %r', name)
    kitten = Kitten.get_by(name=name)
    if not kitten:
      raise http.NotFound()
    return {'kitten': kitten}
  
  def update(self, name, original_name=None, **params):
    if original_name and original_name != name:
      kitten = Kitten.get_by(name=original_name)
      kitten.name = name
    else:
      kitten = Kitten.get_by(name=name)
    kitten.from_dict(params)
    log.info('updated kitten %r', kitten)
    redirect_to(self.read, kitten)
  
  def delete(self, name):
    log.info('deleting kitten %r', name)
    kitten = Kitten.get_by(name=name)
    kitten.delete()
    redirect_to(self)

if __name__ == '__main__':
  main(config='kittens')