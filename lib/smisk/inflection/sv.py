#!/usr/bin/env python
# encoding: utf-8
'''
Swedish

:Author: Rasmus Andersson
'''
__docformat__ = 'restructuredtext en'
__revision__ = '$Revision: 0 $'.split(' ')[1]

import re
from smisk.inflection import Inflector

__all__ = ['inflection']

class SVInflector(Inflector):
  def ordinalize(self, number):
    i = int(number)
    if i % 10 in [1,2]:
      return str(i)+":a"
    else:
      return str(i)+":e"
  

def rc(pat, ignore_case=1):
  if ignore_case:
    return re.compile(pat, re.I)
  else:
    return re.compile(pat)

# Rules based on http://en.wiktionary.org/wiki/Wiktionary:Swedish_inflection_templates
inflection = SVInflector('sv', 'sv_SV')

inflection.regular(r"$", 'a', r"a$") # svensk -a, vanlig -a, stor -a
inflection.regular(r'a$', r'or', r'or$', r'a') # kvinn a-or, mors a-or, flick a-or
inflection.regular(r"e$", 'ar', r"ar$", r'e') # ...
inflection.regular(r"([st]t|o?n)$", r'\1er', r"er$") # katt -er, ven -er, person -er
inflection.regular(r"(ng|il|åt)$", r'\1ar', r"ar$") # peng -ar, bil -ar, båt -ar
inflection.regular(r"(um)$", r'\1ma', r"ma$") # stum -ma, dum -ma
inflection.regular(r"(un)$", r'\1nar', r"nar$") # mun -nar
inflection.regular(r"(ud)$", r'\1en', r"en$") # huvud -en
inflection.regular(r"(ne)$", r'\1n', r"(ne)n$", r'\1') # vittne -n
inflection.regular(r"(iv)en$", r'\1na', r"(iv)na$", r'\1en') # giv en-na
inflection.regular(r"(os)$", r'\1or', r"(os)or$", r'\1') # ros -or
inflection.regular(r"us$", r'öss', r"öss$", r'us') # l us-öss, m us-öss
inflection.regular(r"and$", r'änder', r"änder$", r'and') # h and-änder, l and-änder
inflection.regular(r"(k)el$", r'\1lar', r"(k)lar$", r'\1el') # snork el-lar

inflection.irregular('man', 'män')
inflection.irregular('fader', 'fädrar')
inflection.irregular('moder', 'mödrar')
inflection.irregular('lust', 'lustar')
inflection.irregular('pojk', 'pojkar')
inflection.irregular('pojke', 'pojkar')
inflection.irregular('us', 'öss', False) # l us-öss, m us-öss
inflection.irregular('and', 'änder', False) # h and-änder, l and-änder, str and-änder
inflection.irregular('korn', 'korn') # riskorn, majskorn, korn, etc...
inflection.irregular('liten', 'små', False)

inflection.uncountable('folk','ris','får','sex','lokomotiv','lok','rum',
'barn','förtjusande','brev','hus','gift')

if __name__ == '__main__':
  import unittest
  from smisk.test.inflection import Swedish
  unittest.TextTestRunner().run(unittest.makeSuite(Swedish))
