#!/usr/bin/env python
# encoding: utf-8
'''English
'''
import re
from smisk.inflection import Inflector

__all__ = ['inflection']

inflection = Inflector('en', 'en_EN', 'eng')

inflection.plural(re.compile(ur"$"), u's')
inflection.plural(re.compile(ur"s$", re.I), u's')
inflection.plural(re.compile(ur"(ax|test)is$", re.I), ur'\1es')
inflection.plural(re.compile(ur"(octop|vir)us$", re.I), ur'\1i')
inflection.plural(re.compile(ur"(alias|status)$", re.I), ur'\1es')
inflection.plural(re.compile(ur"(bu)s$", re.I), ur'\1ses')
inflection.plural(re.compile(ur"(buffal|tomat)o$", re.I), ur'\1oes')
inflection.plural(re.compile(ur"([ti])um$", re.I), ur'\1a')
inflection.plural(re.compile(ur"sis$", re.I), u'ses')
inflection.plural(re.compile(ur"(?:([^f])fe|([lr])f)$", re.I), ur'\1\2ves')
inflection.plural(re.compile(ur"(hive)$", re.I), ur'\1s')
inflection.plural(re.compile(ur"([^aeiouy]|qu)y$", re.I), ur'\1ies')
inflection.plural(re.compile(ur"(x|ch|ss|sh)$", re.I), ur'\1es')
inflection.plural(re.compile(ur"(matr|vert|ind)(?:ix|ex)$", re.I), ur'\1ices')
inflection.plural(re.compile(ur"([m|l])ouse$", re.I), ur'\1ice')
inflection.plural(re.compile(ur"^(ox)$", re.I), ur'\1en')
inflection.plural(re.compile(ur"(quiz)$", re.I), ur'\1zes')

inflection.singular(re.compile(ur"s$", re.I), u'')
inflection.singular(re.compile(ur"(n)ews$", re.I), ur'\1ews')
inflection.singular(re.compile(ur"([ti])a$", re.I), ur'\1um')
inflection.singular(re.compile(ur"((a)naly|(b)a|(d)iagno|(p)arenthe|(p)rogno|(s)ynop|(t)he)ses$", re.I), ur'\1\2sis')
inflection.singular(re.compile(ur"(^analy)ses$", re.I), ur'\1sis')
inflection.singular(re.compile(ur"([^f])ves$", re.I), ur'\1fe')
inflection.singular(re.compile(ur"(hive)s$", re.I), ur'\1')
inflection.singular(re.compile(ur"(tive)s$", re.I), ur'\1')
inflection.singular(re.compile(ur"([lr])ves$", re.I), ur'\1f')
inflection.singular(re.compile(ur"([^aeiouy]|qu)ies$", re.I), ur'\1y')
inflection.singular(re.compile(ur"(s)eries$", re.I), ur'\1eries')
inflection.singular(re.compile(ur"(m)ovies$", re.I), ur'\1ovie')
inflection.singular(re.compile(ur"(x|ch|ss|sh)es$", re.I), ur'\1')
inflection.singular(re.compile(ur"([m|l])ice$", re.I), ur'\1ouse')
inflection.singular(re.compile(ur"(bus)es$", re.I), ur'\1')
inflection.singular(re.compile(ur"(o)es$", re.I), ur'\1')
inflection.singular(re.compile(ur"(shoe)s$", re.I), ur'\1')
inflection.singular(re.compile(ur"(cris|ax|test)es$", re.I), ur'\1is')
inflection.singular(re.compile(ur"(octop|vir)i$", re.I), ur'\1us')
inflection.singular(re.compile(ur"(alias|status)es$", re.I), ur'\1')
inflection.singular(re.compile(ur"^(ox)en", re.I), ur'\1')
inflection.singular(re.compile(ur"(vert|ind)ices$", re.I), ur'\1ex')
inflection.singular(re.compile(ur"(matr)ices$", re.I), ur'\1ix')
inflection.singular(re.compile(ur"(quiz)zes$", re.I), ur'\1')

inflection.irregular(u'person', u'people')
inflection.irregular(u'man', u'men')
inflection.irregular(u'child', u'children')
inflection.irregular(u'sex', u'sexes')
inflection.irregular(u'move', u'moves')

inflection.uncountable(u'equipment',u'information',u'rice',u'money',u'species',u'series',
u'fish',u'sheep',u'commotion')
