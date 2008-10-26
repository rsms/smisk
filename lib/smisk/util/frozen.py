# encoding: utf-8
'''Immutable types
'''

__all__ = ['frozendict']

class frozendict(dict):
  '''Immutable dictionary.
  '''
  def __setitem__(self, *args, **kwargs):
    raise TypeError("'frozendict' object does not support item assignment")
  
  setdefault = __delitem__ = clear = pop = popitem = __setitem__
  
  def update(self, *args):
    '''Update a mutable copy with key/value pairs from b, replacing existing keys.
    
    :returns: A mutable copy with updated pairs.
    :rtype: dict
    '''
    d = self.copy()
    d.update(*args)
    return d
  
  copy = dict.copy
  '''Returns a mutable copy.
  '''
  
  def __hash__(self):
    items = self.items()
    res = hash(items[0])
    for item in items[1:]:
      res ^= hash(item)
    return res
  
