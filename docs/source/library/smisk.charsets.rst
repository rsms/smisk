charsets
===========================================================

.. module:: smisk.charsets
.. versionadded:: 1.1.0

Character encodings


.. attribute:: charsets

  Collection of all available character encodings.
  
  Each pair is keyed by the primary name of the encoding and have a dictionary value containing aliases and name of natural languages normally expressed using that encoding::
  
    charsets = {
      #...
      u'iso2022_jp_2': {
        u'alias': u'iso2022jp-2, iso-2022-jp-2',
        u'language': u'Japanese, Korean, Simplified Chinese, Western Europe, Greek'
      },
      #...
    }
  
  **Implementation note:**
  
  At import-time, the vast collection of character sets are inspected and those which are not available on the current system are removed from the *charsets* dict.
  
  :type: dict
