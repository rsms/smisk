#!/usr/bin/env python
# encoding: utf-8

import logging
log = logging.getLogger(__name__)

def expose(template=None):
  def entangle(func):
    if template is not None:
      func.template = template
    return func
  return entangle

def hide():
  def entangle(func):
    log.debug("hiding %s" % func)
    func.hidden = True
    return func
  return entangle

