#!/usr/bin/env python
# encoding: utf-8
from smisk.test import *
from smisk.config import *
import logging
log = logging.getLogger(__name__)
FILESDIR = os.path.join(os.path.dirname(__file__), 'config-support')

class ConfigTests(TestCase):
  def test1_basics(self):
    log.info('--RESET--')
    config.reset()
    self.assertTrue(isinstance(config, dict))
    self.assertTrue(isinstance(config.sources, list))
    self.assertTrue(isinstance(config.default_symbols, dict))
    self.assertTrue(isinstance(config.defaults, dict))
    self.assertEquals(config.get('sdg', None), None)
  
  def _load_simple(self):
    config.loads('''
    "some_key": 456,
    "logging": {
      "": "INFO",
      'foo.bar': INFO
    }
    ''')
  
  def test2_simple_loads_and_get(self):
    log.info('--RESET--')
    config.reset()
    self._load_simple()
    self.assertEquals(config['some_key'], 456)
    self.assertEquals(config['logging'], {'foo.bar': logging.INFO, '':'INFO'})
    self.assertRaises(KeyError, lambda: config['not_here'])
  
  def _load_simple_overload(self):
    config.loads('''
    "some_key": 123,
    "logging": {
      'foo.bar': ERROR
    }''')
  
  def test03_overload(self):
    log.info('--RESET--')
    config.reset()
    self._load_simple()
    self._load_simple_overload()
    self.assertEquals(config['some_key'], 123)
    self.assertEquals(config['logging'], {'foo.bar': logging.ERROR, '':'INFO'})
    self.assertEquals(config['logging']['foo.bar'], logging.ERROR)
  
  def test04_defaults(self):
    log.info('--RESET--')
    config.reset()
    self._load_simple()
    self._load_simple_overload()
    self.assertEquals(config.defaults, {})
    config.defaults = {'my_key': 'internets'}
    self.assertEquals(config.defaults, {'my_key': 'internets'})
    self.assertTrue('my_key' in config)
    self.assertEquals(config['my_key'], 'internets')
    config.loads('"my_key": 123')
    self.assertEquals(config['my_key'], 123)
    config.reload()
    self.assertEquals(config['my_key'], 123)
  
  def test05_file_basics(self):
    log.info('--RESET--')
    config.reset()
    config.load(os.path.join(FILESDIR, 'simple.conf'))
    self.assertContains(config.keys(), ['key1', 'key2', 'key3'])
    self.assertEquals(config['key1'], 'value1')
    self.assertEquals(config['key2'], 12345.6789)
    self.assertEquals(config['key3'], [1,2,3,'4','5'])
  
  def test06_file_include(self):
    log.info('--RESET--')
    config.reset()
    config.load(os.path.join(FILESDIR, 'include.conf'))
    self.assertEquals(config['key1'], 'value1')
    self.assertEquals(config['key2'], 12345.6789)
    self.assertEquals(config['key3'], [1,2,3,'4','5'])
    self.assertEquals(config['key4'], 'Hello')
  
  def test07_file_include_max(self):
    log.info('--RESET--')
    config.reset()
    config.max_include_depth = 5
    path = os.path.join(FILESDIR, 'include-recursive.conf')
    # should raise RuntimeError: maximum include depth exceeded
    self.assertRaises(RuntimeError, lambda: config.load(path))
  
  def test08_file_include_deep(self):
    log.info('--RESET--')
    config.reset()
    config.max_include_depth = 5
    config.load(os.path.join(FILESDIR, 'include-deep1.conf'))
    self.assertEquals(config['key1'], 1)
    self.assertEquals(config['key2'], 22)
    self.assertEquals(config['key3'], 333)
    self.assertEquals(config['key4'], 4444)
    self.assertEquals(config['key5'], 55555)
  
  def test09_file_inherit(self):
    log.info('--RESET--')
    config.reset()
    config.load(os.path.join(FILESDIR, 'inherit.conf'))
    self.assertEquals(config['key1'], 'value1')
    self.assertEquals(config['key2'], 987654) # difference from test6_file_include
    self.assertEquals(config['key3'], [1,2,3,'4','5'])
    self.assertEquals(config['key4'], 'Hello')
  
  def test10_file_inherit_deep(self):
    log.info('--RESET--')
    config.reset()
    config.max_include_depth = 5
    config.load(os.path.join(FILESDIR, 'inherit-deep5.conf'))
    self.assertEquals(config['key1'], 1)
    self.assertEquals(config['key2'], 22)
    self.assertEquals(config['key3'], 333)
    self.assertEquals(config['key4'], 4444)
    self.assertEquals(config['key5'], 55555)
  
  def test11_file_include_glob(self):
    log.info('--RESET--')
    config.reset()
    config.load(os.path.join(FILESDIR, 'include-glob.conf'))
    self.assertEquals(config['key1'], 1)
    self.assertEquals(config['key2'], 22)
    self.assertEquals(config['key3'], 333)
    self.assertEquals(config['key4'], 4444)
    self.assertEquals(config['key5'], 55555)
  
  def test12_file_inherit_glob(self):
    log.info('--RESET--')
    config.reset()
    config.max_include_depth = 5
    config.load(os.path.join(FILESDIR, 'inherit-glob.conf'))
    self.assertEquals(config['key1'], 1)
    self.assertEquals(config['key2'], 22)
    self.assertEquals(config['key3'], 333)
    self.assertEquals(config['key4'], 4444)
    self.assertEquals(config['key5'], 55555)
  


#logging.basicConfig(level=logging.DEBUG, format='%(message)s')

def suite():
  suites = []
  if os.path.isdir(FILESDIR):
    suites = [unittest.makeSuite(ConfigTests)]
  return unittest.TestSuite(suites)

def test():
  runner = unittest.TextTestRunner()
  return runner.run(suite())

if __name__ == "__main__":
  test()
