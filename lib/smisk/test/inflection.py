#!/usr/bin/env python
# encoding: utf-8
from smisk.test import *
from smisk.inflection import inflection as en

class English(TestCase):
  def test_plural(self):
    assert en.pluralize(u'mouse') == u'mice'
    assert en.pluralize(u'train') == u'trains'
    assert en.pluralize(u'commotion') == u'commotion'
    assert en.pluralize(u'cat') == u'cats'
  def test_camel(self):
    assert en.camelize(u'moder_controller/barn') == u'ModerController.Barn'
  def test_human(self):
    assert en.humanize(u'employee_salary') == u'Employee salary'
    assert en.humanize(u'author_id') == u'Author'
  def test_demodule(self):
    assert en.demodulize(u'ActiveRecord.CoreExtensions.String.Inflection') == u'Inflection'
    assert en.demodulize(u'Inflection') == u'Inflection'
  def test_table(self):
    assert en.tableize(u'RawScaledScorer') == u'raw_scaled_scorers'
    assert en.tableize(u'egg_and_ham') == u'egg_and_hams'
    assert en.tableize(u'fancyCategory') == u'fancy_categories'
  def test_class(self):
    assert en.classify(u'egg_and_hams') == u'EggAndHam'
    assert en.classify(u'post') == u'Post'
    assert en.classify(u'categories') == u'Category'
  def test_foreignKey(self):
    assert en.foreignKey(u'Message') == u'message_id'
    assert en.foreignKey(u'Message', False) == u'messageid'
    assert en.foreignKey(u'admin.Post') == u'post_id'
  def test_ordinal(self):
    assert en.ordinalize(1) == u"1st"
    assert en.ordinalize(2) == u"2nd"
    assert en.ordinalize(3) == u"3rd"
    assert en.ordinalize(8) == u"8th"
    assert en.ordinalize(12) == u"12th"
    assert en.ordinalize(1002) == u"1002nd"
    assert en.ordinalize(9876) == u"9876th"
  def test_misc(self):
    assert en.underscore(u'ModerController.Barn') == u'moder_controller/barn'
  

#from smisk.inflection.sv import inflection as sv
#class Swedish(TestCase):
#  def test_plural(self):
#    assert sv.pluralize(u'mus') == u'möss'
#    assert sv.pluralize(u'train') == u'trainer'
#    assert sv.pluralize(u'post') == u'poster'
#    assert sv.pluralize(u'person') == u'personer'
#  
#  def test_dual(self):
#    def t(singular, plural):
#      #print singular, u"->", sv.pluralize(singular) + u',', plural, u'->', sv.singularize(plural)
#      assert sv.pluralize(singular) == plural
#      assert sv.singularize(plural) == singular
#    t(u"bil", u"bilar")
#    t(u"båt", u"båtar")
#    t(u"katt", u"katter")
#    t(u"peng", u"pengar")
#    t(u"man", u"män")
#    t(u"person", u"personer")
#    t(u"huvud", u"huvuden")
#    t(u"folk", u"folk")
#    t(u"vittne", u"vittnen")
#    t(u"morsa", u"morsor")
#    t(u"liten", u"små")
#    t(u"stor", u"stora")
#    t(u"ny", u"nya")
#    t(u"rik", u"rika")
#    t(u"dum", u"dumma")
#    t(u"stum", u"stumma")
#    t(u"kvinna", u"kvinnor")
#    t(u"intressant", u"intressanta")
#    t(u"given", u"givna")
#    t(u"ven", u"vener")
#    t(u"hand", u"händer")
#    t(u"land", u"länder")
#    t(u"kviga", u"kvigor")
#    t(u"mun", u"munnar")
#    t(u"ros", u"rosor")
#    t(u"lus", u"löss")
#    t(u"mus", u"möss")
#    t(u"kust", u"kuster")
#    t(u"lust", u"lustar")
#    t(u"pojke", u"pojkar")
#    t(u"flicka", u"flickor")
#    t(u"snorkel", u"snorklar")
#  
#  def test_ordinal(self):
#    assert sv.ordinalize(1) == u"1:a"
#    assert sv.ordinalize(2) == u"2:a"
#    assert sv.ordinalize(3) == u"3:e"
#    assert sv.ordinalize(921.3) == u"921:a"
#    assert sv.ordinalize(500) == u"500:e"
#  

def suite():
  return unittest.TestSuite([
    unittest.makeSuite(English),
    #unittest.makeSuite(Swedish),
  ])

def test():
  runner = unittest.TextTestRunner()
  return runner.run(suite())

if __name__ == "__main__":
  test()
