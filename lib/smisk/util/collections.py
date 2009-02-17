# encoding: utf-8
'''Collection utilities
'''

__all__ = ['unique_wild', 'unique']

def unique_wild(seq):
  '''
  :param seq:
  :type  seq: collection
  :rtype: list
  '''
  # Not order preserving but faster than list_unique
  return list(set(seq))


def unique(seq):
  '''Return a list of the elements in `seq`, but without duplicates.
  
  For example, ``unique([1,2,3,1,2,3])`` is some permutation of ``[1,2,3]``,
  ``unique("abcabc")`` some permutation of ``["a", "b", "c"]``, and
  ``unique(([1, 2], [2, 3], [1, 2]))`` some permutation of
  ``[[2, 3], [1, 2]]``.
  
  For best speed, all sequence elements should be hashable. Then
  ``unique()`` will usually work in linear time.
  
  If not possible, the sequence elements should enjoy a total
  ordering, and if ``list(s).sort()`` doesn't raise ``TypeError`` it's
  assumed that they do enjoy a total ordering. Then ``unique()`` will
  usually work in ``O(N*log2(N))`` time.
  
  If that's not possible either, the sequence elements must support
  equality-testing. Then ``unique()`` will usually work in quadratic
  time.
  
  :param seq:
  :type  seq: collection
  :rtype: list
  '''
  n = len(seq)
  if n == 0:
    return []
  # Try using a dict first, as that's the fastest and will usually
  # work.  If it doesn't work, it will usually fail quickly, so it
  # usually doesn't cost much to *try* it.  It requires that all the
  # sequence elements be hashable, and support equality comparison.
  u = {}
  try:
    for x in seq:
      u[x] = 1
  except TypeError:
    del u  # move on to the next method
  else:
    return u.keys()
  # We can't hash all the elements.  Second fastest is to sort,
  # which brings the equal elements together; then duplicates are
  # easy to weed out in a single pass.
  # NOTE:  Python's list.sort() was designed to be efficient in the
  # presence of many duplicate elements.  This isn't true of all
  # sort functions in all languages or libraries, so this approach
  # is more effective in Python than it may be elsewhere.
  try:
    t = list(seq)
    t.sort()
  except TypeError:
    del t  # move on to the next method
  else:
    assert n > 0
    last = t[0]
    lasti = i = 1
    while i < n:
      if t[i] != last:
        t[lasti] = last = t[i]
        lasti += 1
      i += 1
    return t[:lasti]
  
  # Brute force is all that's left.
  u = []
  for x in seq:
    if x not in u:
      u.append(x)
  return u

def merge(a, b):
  '''Updates collection `a` with contents of collection `b`, recursively
  merging any lists and dictionaries.
  
  Lists are merged through a.extend(b), dictionaries are merged by replacing
  and non-list or dict key with the value from collection b. In other words,
  collection b takes precedence.
  '''
  if isinstance(a, list):
    a.extend(b)
    return a
  elif isinstance(a, dict):
    return merge_dict(a, b)
  else:
    raise TypeError('first argument must be a list or a dict')

def merge_dict(a, b, merge_lists=True):
  '''Updates dictionary `a` with contents of dictionary `b`, recursively
  merging any lists and dictionaries.
  
  Lists are merged through a.extend(b), dictionaries are merged by replacing
  and non-list or dict key with the value from collection b. In other words,
  collection b takes precedence.
  '''
  for bk,bv in b.items():
    if a.has_key(bk) and hasattr(bv, 'has_key') and hasattr(a[bk], 'has_key'):
      merge_dict(a[bk], bv, merge_lists)
    elif merge_lists and hasattr(bv, 'extend') and hasattr(a.get(bk), 'extend'):
      a[bk].extend(bv)
    else:
      a[bk] = bv
  return a

def merged(a, b):
  '''Like merge but does not modify *a*
  '''
  if isinstance(a, (list,tuple)):
    return a + b
  elif isinstance(a, dict):
    return merged_dict(a, b)
  else:
    raise TypeError('first argument must be a list or a dict')

def merged_dict(a, b, merge_lists=True):
  '''Like merge_dict but does not modify *a*
  '''
  a = a.copy()
  for bk,bv in b.items():
    if a.has_key(bk) and hasattr(bv, 'has_key') and hasattr(a[bk], 'has_key'):
      a[bk] = merged_dict(a[bk], bv, merge_lists)
    elif merge_lists and hasattr(bv, 'extend') and hasattr(a.get(bk), 'extend'):
      a[bk] = a[bk] + bv
    else:
      a[bk] = bv
  return a
