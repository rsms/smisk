#!/usr/bin/env python
# encoding: utf-8
from smisk.mvc import *
from smisk.mvc.model import *

class Kitten(Entity):
  name = Field(Unicode(255), primary_key=True)
  color = Field(Unicode(30))
  year_born = Field(Integer)

class root(Controller):
  def __call__(self, *args, **params):
    kittens = [dict(k) for k in Kitten.query.all()]
    return {'kittens': kittens}

  def create(self, name, **params):
    kitten = Kitten(name=name, **params)
    redirect_to(u'/read?name=%s' % kitten.name)
  
  def read(self, name):
    kitten = Kitten.get_by(name=name)
    return kitten.to_dict()
  
  def update(self, name, color=Undefined, year_born=Undefined):
    kitten = Kitten.get_by(name=name)
    if color is not Undefined:
      kitten.color = color
    if year_born is not Undefined:
      kitten.year_born = year_born
    redirect_to(read, name=kitten.name)
  
  def delete(self, name):
    kitten = Kitten.get_by(name=name)
    kitten.delete()
    redirect_to('/')

if __name__ == '__main__':
  main(config='kittens')