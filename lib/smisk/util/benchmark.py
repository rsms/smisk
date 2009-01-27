# encoding: utf-8
import itertools, gc, sys, resource, time

__all__ = ['benchmark']

def benchmark(name='benchmark', iterations=1000000, outfp=sys.stderr, it_subtractor=0.0):
  '''Measure raw performance.
  '''
  def fmt(sec):
    return "%3.0f sec  %3.0f ms  %4.0f us" % (sec, (sec*1000)%1000, (sec*1000000)%1000)
  gcold = gc.isenabled()
  gc.disable()
  it = itertools.repeat(None, iterations)
  u0 = resource.getrusage(resource.RUSAGE_SELF)
  real = time.time()
  exc = None
  try:
    for x in it:
      yield x
  except Exception, e:
    exc = e
  real = time.time() - real
  u1 = resource.getrusage(resource.RUSAGE_SELF)
  if gcold:
    gc.enable()
  if it_subtractor > 0.0:
    real -= it_subtractor * float(iterations)
  outfp.flush()
  print >> outfp, '\n%s:  %6.1f calls/sec' % (name, iterations/real)
  print >> outfp, '-----------------------------------'
  print >> outfp, 'avg. call ', fmt(real/iterations)
  print >> outfp, '-----------------------------------'
  print >> outfp, 'real      ', fmt(real)
  print >> outfp, 'user      ', fmt(u1.ru_utime - u0.ru_utime)
  print >> outfp, 'system    ', fmt(u1.ru_stime - u0.ru_stime)
  outfp.flush()
  if exc:
    raise exc

