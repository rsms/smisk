#!/usr/bin/env python
# encoding: utf-8
from distutils.core import setup, Extension

setup (name = "pingpong",
	version = "1.0",
	maintainer = "Rasmus Andersson",
	maintainer_email = "rasmus@flajm.se",
	description = "Simple python C module",
	ext_modules = [Extension('pingpong',
		sources=['pingpong.c'])]
)