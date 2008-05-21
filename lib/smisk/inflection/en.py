#!/usr/bin/env python
# encoding: utf-8
"""
English inflections
"""
if __name__ == '__main__': print "Can't be run directly"
__docformat__ = 'restructuredtext en'
__revision__ = '$Revision: 0$'.split(' ')[1][:-1]

import re
from . import Inflector

__all__ = ['inflection']

inflection = Inflector('en', 'en_EN', 'eng')

inflection.plural(re.compile(r"$"), 's')
inflection.plural(re.compile(r"s$", re.I), 's')
inflection.plural(re.compile(r"(ax|test)is$", re.I), r'\1es')
inflection.plural(re.compile(r"(octop|vir)us$", re.I), r'\1i')
inflection.plural(re.compile(r"(alias|status)$", re.I), r'\1es')
inflection.plural(re.compile(r"(bu)s$", re.I), r'\1ses')
inflection.plural(re.compile(r"(buffal|tomat)o$", re.I), r'\1oes')
inflection.plural(re.compile(r"([ti])um$", re.I), r'\1a')
inflection.plural(re.compile(r"sis$", re.I), 'ses')
inflection.plural(re.compile(r"(?:([^f])fe|([lr])f)$", re.I), r'\1\2ves')
inflection.plural(re.compile(r"(hive)$", re.I), r'\1s')
inflection.plural(re.compile(r"([^aeiouy]|qu)y$", re.I), r'\1ies')
inflection.plural(re.compile(r"(x|ch|ss|sh)$", re.I), r'\1es')
inflection.plural(re.compile(r"(matr|vert|ind)(?:ix|ex)$", re.I), r'\1ices')
inflection.plural(re.compile(r"([m|l])ouse$", re.I), r'\1ice')
inflection.plural(re.compile(r"^(ox)$", re.I), r'\1en')
inflection.plural(re.compile(r"(quiz)$", re.I), r'\1zes')

inflection.singular(re.compile(r"s$", re.I), '')
inflection.singular(re.compile(r"(n)ews$", re.I), r'\1ews')
inflection.singular(re.compile(r"([ti])a$", re.I), r'\1um')
inflection.singular(re.compile(r"((a)naly|(b)a|(d)iagno|(p)arenthe|(p)rogno|(s)ynop|(t)he)ses$", re.I), r'\1\2sis')
inflection.singular(re.compile(r"(^analy)ses$", re.I), r'\1sis')
inflection.singular(re.compile(r"([^f])ves$", re.I), r'\1fe')
inflection.singular(re.compile(r"(hive)s$", re.I), r'\1')
inflection.singular(re.compile(r"(tive)s$", re.I), r'\1')
inflection.singular(re.compile(r"([lr])ves$", re.I), r'\1f')
inflection.singular(re.compile(r"([^aeiouy]|qu)ies$", re.I), r'\1y')
inflection.singular(re.compile(r"(s)eries$", re.I), r'\1eries')
inflection.singular(re.compile(r"(m)ovies$", re.I), r'\1ovie')
inflection.singular(re.compile(r"(x|ch|ss|sh)es$", re.I), r'\1')
inflection.singular(re.compile(r"([m|l])ice$", re.I), r'\1ouse')
inflection.singular(re.compile(r"(bus)es$", re.I), r'\1')
inflection.singular(re.compile(r"(o)es$", re.I), r'\1')
inflection.singular(re.compile(r"(shoe)s$", re.I), r'\1')
inflection.singular(re.compile(r"(cris|ax|test)es$", re.I), r'\1is')
inflection.singular(re.compile(r"(octop|vir)i$", re.I), r'\1us')
inflection.singular(re.compile(r"(alias|status)es$", re.I), r'\1')
inflection.singular(re.compile(r"^(ox)en", re.I), r'\1')
inflection.singular(re.compile(r"(vert|ind)ices$", re.I), r'\1ex')
inflection.singular(re.compile(r"(matr)ices$", re.I), r'\1ix')
inflection.singular(re.compile(r"(quiz)zes$", re.I), r'\1')

inflection.irregular('person', 'people')
inflection.irregular('man', 'men')
inflection.irregular('child', 'children')
inflection.irregular('sex', 'sexes')
inflection.irregular('move', 'moves')

inflection.uncountable('equipment','information','rice','money','species','series',
'fish','sheep','commotion')
