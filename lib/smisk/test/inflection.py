#!/usr/bin/env python
# encoding: utf-8
import unittest
from inflection import inflection as en

class English(unittest.TestCase):
	def test_plural(self):
		assert en.pluralize('mouse') == 'mice'
		assert en.pluralize('train') == 'trains'
		assert en.pluralize('commotion') == 'commotion'
		assert en.pluralize('cat') == 'cats'
	def test_camel(self):
		assert en.camelize('moder_controller/barn') == 'ModerController.Barn'
	def test_human(self):
		assert en.humanize('employee_salary') == 'Employee salary'
		assert en.humanize('author_id') == 'Author'
	def test_demodule(self):
		assert en.demodulize('ActiveRecord.CoreExtensions.String.Inflection') == 'Inflection'
		assert en.demodulize('Inflection') == 'Inflection'
	def test_table(self):
		assert en.tableize('RawScaledScorer') == 'raw_scaled_scorers'
		assert en.tableize('egg_and_ham') == 'egg_and_hams'
		assert en.tableize('fancyCategory') == 'fancy_categories'
	def test_class(self):
		assert en.classify('egg_and_hams') == 'EggAndHam'
		assert en.classify('post') == 'Post'
		assert en.classify('categories') == 'Category'
	def test_foreignKey(self):
		assert en.foreignKey('Message') == 'message_id'
		assert en.foreignKey('Message', False) == 'messageid'
		assert en.foreignKey('admin.Post') == 'post_id'
	def test_ordinal(self):
		assert en.ordinalize(1) == "1st"
		assert en.ordinalize(2) == "2nd"
		assert en.ordinalize(3) == "3rd"
		assert en.ordinalize(8) == "8th"
		assert en.ordinalize(12) == "12th"
		assert en.ordinalize(1002) == "1002nd"
		assert en.ordinalize(9876) == "9876th"
	def test_misc(self):
		assert en.underscore('ModerController.Barn') == 'moder_controller/barn'
	

from inflection.sv import inflection as sv
class Swedish(unittest.TestCase):
	def test_plural(self):
		assert sv.pluralize('mouse') == 'mice'
		assert sv.pluralize('train') == 'trains'
		assert sv.pluralize('commotion') == 'commotion'
		assert sv.pluralize('cat') == 'cats'
	def test_ordinal(self):
		assert sv.ordinalize(1) == "1:a"
		assert sv.ordinalize(2) == "2:a"
		assert sv.ordinalize(3) == "3:e"
		assert sv.ordinalize(921.3) == "921:a"
		assert sv.ordinalize(500) == "500:e"
	

def suite():
  return unittest.TestSuite([
    unittest.makeSuite(English),
    unittest.makeSuite(Swedish),
  ])

def test():
  runner = unittest.TextTestRunner()
  return runner.run(suite())

if __name__ == "__main__":
  test()
