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

  def create(self, name, color=None, year_born=None):
    kitten = Kitten(name=name, color=color, year_born=year_born)
    redirect_to(self.read, kitten)
  
  def read(self, name):
    kitten = Kitten.get_by(name=name)
    return kitten.to_dict()
  
  def update(self, name, **params):
    kitten = Kitten.get_by(name=name)
    kitten.from_dict(params)
    redirect_to(self.read, kitten)
  
  def delete(self, name):
    kitten = Kitten.get_by(name=name)
    kitten.delete()
    redirect_to(self)

if __name__ == '__main__':
  main(config='kittens')