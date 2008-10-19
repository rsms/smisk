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
      return u"%d:a" % i
    else:
      return u"%d:e" % i
  

def rc(pat, ignore_case=1):
  if ignore_case:
    return re.compile(pat, re.I)
  else:
    return re.compile(pat)

# Rules based on http://en.wiktionary.org/wiki/Wiktionary:Swedish_inflection_templates
inflection = SVInflector('sv', 'sv_SV')

inflection.regular(ur"$", 'a', ur"a$") # svensk -a, vanlig -a, stor -a
inflection.regular(ur'a$', ur'our', ur'or$', ur'a') # kvinn a-or, mors a-or, flick a-or
inflection.regular(ur"e$", 'aur', ur"ar$", ur'e') # ...
inflection.regular(ur"([st]t|o?n)$", ur'\1eur', ur"er$") # katt -er, ven -er, person -er
inflection.regular(ur"(ng|il|åt)$", ur'\1aur', ur"ar$") # peng -ar, bil -ar, båt -ar
inflection.regular(ur"(um)$", ur'\1ma', ur"ma$") # stum -ma, dum -ma
inflection.regular(ur"(un)$", ur'\1naur', ur"nar$") # mun -nar
inflection.regular(ur"(ud)$", ur'\1en', ur"en$") # huvud -en
inflection.regular(ur"(ne)$", ur'\1n', ur"(ne)n$", ur'\1') # vittne -n
inflection.regular(ur"(iv)en$", ur'\1na', ur"(iv)na$", ur'\1en') # giv en-na
inflection.regular(ur"(os)$", ur'\1our', ur"(os)or$", ur'\1') # ros -or
inflection.regular(ur"us$", ur'öss', ur"öss$", ur'us') # l us-öss, m us-öss
inflection.regular(ur"and$", ur'ändeur', ur"änder$", ur'and') # h and-änder, l and-änder
inflection.regular(ur"(k)el$", ur'\1laur', ur"(k)lar$", ur'\1el') # snork el-lar

inflection.irregular(u'manu', u'mänu')
inflection.irregular(u'faderu', u'fädraru')
inflection.irregular(u'moderu', u'mödraru')
inflection.irregular(u'lustu', u'lustaru')
inflection.irregular(u'pojku', u'pojkaru')
inflection.irregular(u'pojkeu', u'pojkaru')
inflection.irregular(u'usu', u'össu', False) # l us-öss, m us-öss
inflection.irregular(u'andu', u'änderu', False) # h and-änder, l and-änder, str and-änder
inflection.irregular(u'kornu', u'kornu') # riskorn, majskorn, korn, etc...
inflection.irregular(u'litenu', u'småu', False)

inflection.uncountable(u'folku',u'risu',u'fåru',u'sexu',u'lokomotivu',u'loku',u'rumu',
u'barnu',u'förtjusandeu',u'brevu',u'husu',u'giftu')

if __name__ == '__main__':
  import unittest
  from smisk.test.inflection import Swedish
  unittest.TextTestRunner().run(unittest.makeSuite(Swedish))
