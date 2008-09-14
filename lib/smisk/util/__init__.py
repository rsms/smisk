# encoding: utf-8
import sys, os

class Singleton(object):
  def __new__(type):
    if not '_instance' in type.__dict__:
      type._instance = object.__new__(type)
    return type._instance
  

def unique_sorted_modules_of_items(v):
  s = []
  for t in v:
    s.append(t.__module__)
  s = list_unique_wild(s)
  s.sort()
  return s


def list_python_filenames_in_dir(path, only_py=True):
  names = []
  for fn in os.listdir(path):
    if fn[-3:] == '.py':
      names.append(fn[:-3])
    elif not only_py:
      fn4 = fn[-4:]
      if fn4 == '.pyc' or fn4 == '.pyo':
        names.append(fn[:-4])
  if names:
    if not only_py:
      names = list_unique_wild(names)
    names.sort()
  return names


def find_modules_for_classtree(cls, exclude_root=True, unique=True):
  '''
  Returns a list of all modules in which cls and any subclasses are defined.
  '''
  if exclude_root:
    modules = []
  else:
    modules = [sys.modules[cls.__module__]]
  for subcls in cls.__subclasses__():
    modules.extend(find_modules_for_classtree(subcls, False, False))
  if unique:
    modules = list_unique(modules)
  return modules


def list_unique_wild(seq):
  # Not order preserving but faster than list_unique
  return list(set(seq))


def list_unique(s):
  """Return a list of the elements in s, but without duplicates.
  
  For example, unique([1,2,3,1,2,3]) is some permutation of [1,2,3],
  unique("abcabc") some permutation of ["a", "b", "c"], and
  unique(([1, 2], [2, 3], [1, 2])) some permutation of
  [[2, 3], [1, 2]].
  
  For best speed, all sequence elements should be hashable.  Then
  unique() will usually work in linear time.
  
  If not possible, the sequence elements should enjoy a total
  ordering, and if list(s).sort() doesn't raise TypeError it's
  assumed that they do enjoy a total ordering.  Then unique() will
  usually work in O(N*log2(N)) time.
  
  If that's not possible either, the sequence elements must support
  equality-testing.  Then unique() will usually work in quadratic
  time.
  """
  n = len(s)
  if n == 0:
    return []
  # Try using a dict first, as that's the fastest and will usually
  # work.  If it doesn't work, it will usually fail quickly, so it
  # usually doesn't cost much to *try* it.  It requires that all the
  # sequence elements be hashable, and support equality comparison.
  u = {}
  try:
    for x in s:
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
    t = list(s)
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
  for x in s:
    if x not in u:
      u.append(x)
  return u


def format_exc(exc=None):
  ''':rtype: string'''
  if exc is None:
    exc = sys.exc_info()
  if exc == (None, None, None):
    return ''
  import traceback
  return ''.join(traceback.format_exception(*exc))
