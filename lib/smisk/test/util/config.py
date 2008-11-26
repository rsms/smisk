#!/usr/bin/env python
# encoding: utf-8
from smisk.test import *
from smisk.config import *
import logging

class ConfigTests(TestCase):
  def test1_basics(self):
    self.assertTrue(isinstance(config, dict))
    self.assertTrue(isinstance(config.sources, list))
    self.assertTrue(isinstance(config.default_symbols, dict))
    self.assertTrue(isinstance(config.defaults, dict))
    self.assertEquals(config.get('sdg', None), None)
  
  def test2_simple_loads_and_get(self):
    config.loads('''
    "some_key": 456,
    "logging": {
      "": "INFO",
      'foo.bar': INFO
    }
    ''')
    self.assertEquals(config['some_key'], 456)
    self.assertEquals(config['logging'], {'foo.bar': logging.INFO, '':'INFO'})
    self.assertRaises(KeyError, lambda: config['not_here'])
  
  def test3_overload(self):
    config.loads('''
    "some_key": 123,
    "logging": {
      'foo.bar': ERROR
    }''')
    self.assertEquals(config['some_key'], 123)
    self.assertEquals(config['logging'], {'foo.bar': logging.ERROR, '':'INFO'})
    self.assertEquals(config['logging']['foo.bar'], logging.ERROR)
  
  def test4_defaults(self):
    self.assertEquals(config.defaults, {})
    config.defaults = {'my_key': 'internets'}
    self.assertEquals(config.defaults, {'my_key': 'internets'})
    self.assertTrue('my_key' in config)
    self.assertEquals(config['my_key'], 'internets')
    config.loads('"my_key": 123')
    self.assertEquals(config['my_key'], 123)
    config.reload()
    self.assertEquals(config['my_key'], 123)
  

def suite():
  return unittest.TestSuite([
    unittest.makeSuite(ConfigTests),
  ])

def test():
  runner = unittest.TextTestRunner()
  return runner.run(suite())

if __name__ == "__main__":
  test()
