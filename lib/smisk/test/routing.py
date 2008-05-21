#!/usr/bin/env python
# encoding: utf-8
import unittest
from routing import *

class RoutingTests(unittest.TestCase):
	
	def test1_fixed(self):
		r = Router()
		r.map(None, default=1)
		r.map("/hello", fixed1=1)
		r.map("/hello/bob", fixed2=1)
		assert 'fixed1' in r("/hello")
		assert 'fixed2' in r("/hello/bob")
		assert 'default' in r("/hel")
	
	def test2_prefix(self):
		r = Router()
		r.map("/monkeys*", prefix1=1)
		r.map(None)
		assert 'prefix1' in r("/monkeys")
		assert 'prefix1' in r("/monkeys/bananas.html")
		assert 'prefix1' not in r("/monkey")
	
	def test3_suffix(self):
		r = Router()
		r.map(None)
		r.map("*.html", suffix=1)
		assert 'suffix' in r("/monkeys.html")
		assert 'suffix' in r("/monkeys/bananas.html")
		assert 'suffix' not in r("/monkey")
	
	def test4_regexp(self):
		r = Router()
		r.map(None)
		r.map(re.compile(r"^(?:/(?P<year>[0-9]{4})|)(?:/(?P<month>[0-9]{2})|)(?:/(?P<day>[0-9]{2})|)/?$"), dynamic_time=1)
		r.map(re.compile(r"^/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/(?P<day>[0-9]{2})/?$"), strict_time=1)
		r.map(re.compile(r"^/[a-zA-Z]\w+$"), re1=1)
		assert 're1' in r("/hello")
		assert 'strict_time' not in r("/hello")
		m = r("/hello/")
		assert 're1' not in m
		assert 'strict_time' not in m
		assert 'strict_time' in r("/2007/05/17")
		m = r("/1903/11/22/")
		assert 'strict_time' in m
		assert 'year' in m
		assert 'month' in m
		assert 'day' in m
		assert 'dynamic_time' not in m
		assert 'dynamic_time' in r("/1903/11/")
		m = r("/1903/11")
		assert 'dynamic_time' in m
		assert 'year' in m
		assert 'month' in m
		assert 'day' in m
		assert m['year'] == '1903'
		assert m['month'] == '11'
		assert m['day'] == None
		assert 'dynamic_time' not in r("/1903/1")
		assert 'dynamic_time' in r("/1903/")
		assert 'dynamic_time' in r("/1903")
		assert 'dynamic_time' not in r("/190")
	
	def test5_keyword(self):
		# Since a keyword destination actually is a RegExp destination,
		# we have loosen up on tests here because the RegExpDestination
		# type is tested in test4_regexp.
		r = Router()
		r.map(None)
		r.map("/:controller/:action/:id", kw0=1, action='something')
		m = r("/foo/hello/momo")
		assert 'controller' in m
		assert 'action' in m
		assert 'id' in m
		assert m['controller'] == 'foo'
		assert m['action'] == 'hello'
		assert m['id'] == 'momo'
		r = Router()
		r.map(None)
		r.map("/foo/:bar/:action", kw1=1)
		m = r("/foo/hello/momo")
		assert 'kw1' in m
		assert 'bar' in m
		assert 'action' in m
		assert m['bar'] == 'hello'
		assert m['action'] == 'momo'
		assert 'bar' in r("/foo/hello")
		assert 'bar' not in r("/hej")
	

def suite():
  return unittest.TestSuite([
    unittest.makeSuite(RoutingTests),
  ])

def test():
  runner = unittest.TextTestRunner()
  return runner.run(suite())

if __name__ == "__main__":
  test()
