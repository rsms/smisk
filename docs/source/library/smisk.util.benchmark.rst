benchmark
===========================================================

.. module:: smisk.util.benchmark
.. versionadded:: 1.1.2


Functions
-------------------------------------------------


.. function:: benchmark(name='benchmark', iterations=1000000, outfp=sys.stderr, it_subtractor=0.0)

  Measure raw performance.
  
  Upon iteration end or exception raised, prints time taken and resources used
  to *outfp*.
  
  Example::
    
    from smisk.util.benchmark import benchmark
    
    for x in benchmark('run 1', 10000):
      f = open('/tmp/mos', 'r')
      f.close()
  
