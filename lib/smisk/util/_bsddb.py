# encoding: utf-8
'''Compatibility loader for Python <2.5
'''
# when we drop support for 2.4 we can do absolute imports and do no longer
# need this ugly hack.
from bsddb import *
import bsddb.dbshelve as dbshelve
