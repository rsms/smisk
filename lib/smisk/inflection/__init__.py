#!/usr/bin/env python
# encoding: utf-8
'''
Word transformation.

Transforms words from singular to plural, class names to table names, 
modularized class names to ones without, and class names to foreign keys.

Inflection is language specific and the default `inflection` handles English
language inflection. You can access inflection handlers for other languages
by importing the appropriate inflector. For example
``from miwa.inflection.sv import inflection`` to use Swedish inflection.

.. packagetree::

:Author:          Rasmus Andersson http://hunch.se/
:var inflections: locale-to-Inflection-object map
:var inflection:  English inflection
'''

import re, logging

inflections = {}
log = logging.getLogger(__name__)

class Inflector(object):
  '''Language inflector.
  
  :ivar locales:      languages this inflection handles
  :ivar plurals:      plural rules
  :ivar singulars:    singular rules
  :ivar uncountables: list of uncountable words
  '''
  def __init__(self, *locales):
    '''Create a inflection handler.
    
    Locale codes should comply to:
    * `RFC 1766 <http://www.faqs.org/rfcs/rfc1766.html>`__, preferably as
    * `ISO 639-1 <http://en.wikipedia.org/wiki/ISO_639-1>`__ (two-letter code).
    
    A list of language codes can be found here:
    http://www.loc.gov/standards/iso639-2/php/code_list.php
    
    :param locales: Language codes representing languages this `Inflector` handles.
    :type  locales: string
    '''
    self.plurals = []
    self.singulars = []
    self.uncountables = []
    self.locales = locales
    for locale in locales:
      inflections[locale] = self
  
  
  def plural(self, rule, replacement):
    '''Specifies a new pluralization rule and its replacement.
    
    :type rule:        RegExp pattern
    :type replacement: string
    :rtype: None
    '''
    self.plurals[0:0] = [tuple([rule, replacement])]
  
  
  def singular(self, rule, replacement):
    '''Specifies a new singularization rule and its replacement.
    
    :type rule:        RegExp pattern
    :type replacement: string
    :rtype: None
    '''
    self.singulars[0:0] = [tuple([rule, replacement])]
  
  
  def regular(self, plural_find, plural_replace, singular_find, singular_replace=''):
    '''Specified a new regular inflection.
    
    :param plural_find:      regular expression pattern (which will be compiled)
    :type  plural_find:      string
    :param plural_replace:   replacement (may contain back-references to 
                             regexp groups from ``plural_find``)
    :type  plural_replace:   string
    :param singular_find:    regular expression pattern (which will be compiled)
    :type  singular_find:    string
    :param singular_replace: replacement (may contain back-references to 
                             regexp groups from ``singular_find``)
    :type  singular_replace: string
    :rtype: None
    '''
    self.plural(re.compile(plural_find, re.I), plural_replace)
    self.singular(re.compile(singular_find, re.I), singular_replace)
  
  
  def irregular(self, singular, plural, first_letter_is_the_same=True):
    '''Specifies a new irregular that applies to both pluralization and 
    singularization at the same time.
    
    Examples:
      inf.irregular('octopus', 'octopi')
      inf.irregular('person', 'people')
    
    :type singular: string
    :type plural:   string
    :type first_letter_is_the_same: bool
    :rtype: None
    '''
    if first_letter_is_the_same:
      self.plural(re.compile(ur"(%s)%s$" % (singular[0], singular[1:]), re.IGNORECASE), ur'\1' + plural[1:])
      self.singular(re.compile(ur"(%s)%s$" % (plural[0], plural[1:]), re.IGNORECASE), ur'\1' + singular[1:])
    else:
      self.plural(re.compile(ur"%s$" % singular), plural)
      self.plural(re.compile(ur"%s$" % singular.capitalize()), plural.capitalize())
      self.singular(re.compile(ur"%s$" % plural.capitalize()), singular.capitalize())
      self.singular(re.compile(ur"%s$" % plural), singular)
  
  
  def uncountable(self, *words):
    '''Add uncountable words that shouldn't be attempted inflected.
    
    Examples:
      uncountable "money"
      uncountable "money"), "information"
      uncountable %w( money information rice )
    
    :param words: strings
    :rtype: None
    '''
    self.uncountables[0:0] = [w.lower() for w in words]
  
  
  def clear(self):
    '''Clears any loaded inflections.
    
    :rtype: None
    '''
    self.plurals = []
    self.singulars = []
    self.uncountables = []
  
  
  def pluralize(self, word):
    '''Returns the plural form of the word in the string.
    
    Examples
      "post".pluralize              -> "posts"
      "octopus".pluralize           -> "octopi"
      "sheep".pluralize             -> "sheep"
      "words".pluralize             -> "words"
      "the blue mailman".pluralize  -> "the blue mailmen"
      "CamelOctopus".pluralize      -> "CamelOctopi"
    
    :rtype: unicode
    '''
    word = unicode(word)
    if word.lower() in self.uncountables:
      return word
    else:
      for (rule, replacement) in self.plurals:
        #log.debug("pluralize(): rule: %r, replacement: %r", rule.pattern, replacement)
        m = rule.subn(replacement, word)
        if m[1] > 0:
          return m[0]
    return word
  
  
  def singularize(self, word):
    '''The reverse of pluralize, returns the singular form of a word in a string.
    
    Examples
      "posts".singularize #=> "post"
      "octopi".singularize #=> "octopus"
      "sheep".singluarize #=> "sheep"
      "word".singluarize #=> "word"
      "the blue mailmen".singularize #=> "the blue mailman"
      "CamelOctopi".singularize #=> "CamelOctopus"
    
    :param word: a possibly plural word which should be converted to singular form.
    :rtype: unicode
    '''
    word = unicode(word)
    if word.lower() in self.uncountables:
      return word
    else:
      for (rule, replacement) in self.singulars:
        m = rule.subn(replacement, word)
        if m[1] > 0:
          return m[0]
    return word
  
  def camelize(self, lower_case_and_underscored_word, first_letter_uppercase=True):
    '''By default, camelize converts strings to UpperCamelCase. If the
    ``first_letter_uppercase`` argument is set to False, `camelize` produces
    lowerCamelCase.

    `camelize` will also convert ``/`` to ``.`` which is useful for converting
    paths to namespaces

    Examples
      "active_record".camelize            -> "ActiveRecord"
      "active_record".camelize(False)     -> "activeRecord"
      "active_record/errors".camelize     -> "ActiveRecord.Errors"
      "active_record/errors".camelize(0)  -> "activeRecord.Errors"
    
    :rtype: unicode
    '''
    if first_letter_uppercase:
      p2 = re.compile(ur"(^|_)(.)")
      lower_case_and_underscored_word = Inflector.camelize.re1.sub(
        lambda m: '.' + m.group(1).upper(), lower_case_and_underscored_word)
      return Inflector.camelize.re2.sub(lambda m: m.group(2).upper(), 
        lower_case_and_underscored_word)
    else:
      return lower_case_and_underscored_word[0] + camelize(lower_case_and_underscored_word)[1:]
  camelize.re1 = re.compile(ur"/(.?)")
  camelize.re2 = re.compile(ur"(^|_)(.)")
  
  
  def underscore(self, camel_cased_word):
    '''The reverse of `camelize`. Makes an underscored form from the expression
    in the string.
    
    Changes '.' to '/' to convert namespaces to paths.
    
    Examples
      "ActiveRecord".underscore         -> "active_record"
      "ActiveRecord::Errors".underscore -> active_record/errors
    
    :rtype: unicode
    '''
    return Inflector.underscore.re2.sub(ur'\1_\2', 
      Inflector.underscore.re1.sub(ur'\1_\2',
      camel_cased_word.replace(u'.',u'/'))).replace(u'-',u'_').lower()
  underscore.re1 = re.compile(ur'([A-Z]+)([A-Z][a-z])')
  underscore.re2 = re.compile(ur'([a-z\d])([A-Z])')
  
  
  def humanize(self, lower_case_and_underscored_word):
    '''Capitalizes the first word and turns underscores into spaces and strips _id.
    Like titleize, this is meant for creating pretty output.
    
    Examples
      "employee_salary" -> "Employee salary"
      "author_id"       -> "Author"
    
    :rtype: unicode
    '''
    if len(lower_case_and_underscored_word) >= 3 and lower_case_and_underscored_word[-3:] == '_id':
      lower_case_and_underscored_word = lower_case_and_underscored_word[:-3]
    return lower_case_and_underscored_word.replace('_',' ').capitalize()
  
  
  def demodulize(self, class_name_in_module):
    '''Removes the module part from the expression in the string
    
    Examples
      "ActiveRecord.CoreExtensions.String.Inflectors".demodulize #=> "Inflectors"
      "Inflectors".demodulize #=> "Inflectors"
    
    :rtype: unicode
    '''
    p = class_name_in_module.rfind('.')
    if p != -1:
      return class_name_in_module[p+1:]
    return class_name_in_module
  
  
  def tableize(self, class_name):
    '''Create the name of a table like Rails does for models to table names. This method
    uses the pluralize method on the last word in the string.
    
    Examples
      "RawScaledScorer".tableize  -> "raw_scaled_scorers"
      "egg_and_ham".tableize      -> "egg_and_hams"
      "fancyCategory".tableize    -> "fancy_categories"
    
    :rtype: unicode
    '''
    return self.pluralize(self.underscore(class_name))
  
  
  def classify(self, table_name):
    '''Create a class name from a table name.
    
    Examples
      "egg_and_hams".classify -> "EggAndHam"
      "post".classify         -> "Post"
    
    :rtype: unicode
    '''
    return self.camelize(self.singularize(self.demodulize(table_name)))
  
  
  def foreignKey(self, class_name, separate_class_name_and_id_with_underscore=True):
    '''Creates a foreign key name from a class name.
    +separate_class_name_and_id_with_underscore+ sets whether
    the method should put '_' between the name and 'id'.
    
    Examples
      "Message".foreignKey        -> "message_id"
      "Message".foreignKey(false) -> "messageid"
      "Admin::Post".foreignKey    -> "post_id"
    
    :rtype: unicode
    '''
    return self.underscore(self.demodulize(class_name)) +\
      (separate_class_name_and_id_with_underscore and "_id" or "id")
  
  
  def ordinalize(self, number):
    '''Ordinalize turns a number into an ordinal string used to denote the
    position in an ordered sequence such as 1st, 2nd, 3rd, 4th.
    
    Examples
      ordinalize(1)     -> "1st"
      ordinalize(2)     -> "2nd"
      ordinalize(1002)  -> "1002nd"
      ordinalize(1003)  -> "1003rd"
    
    :rtype: unicode
    '''
    i = int(number)
    if i % 100 in [11,12,13]:
      return u'%dth' % i
    else:
      x = i % 10
      if x == 1:
        return u'%sst' % i
      elif x == 2:
        return u'%dnd' % i
      elif x == 3:
        return u'%drd' % i
      else:
        return u'%dth' % i
  
  

# Load default inflections (English)
from smisk.inflection.en import inflection

if __name__ == '__main__':
  from smisk.test.inflection import test
  test()
