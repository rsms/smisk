# encoding: utf-8
'''Model in MVC
'''
from warnings import filterwarnings, warn
try:
  # Ignore the SA string type depr warning
  from sqlalchemy.exceptions import SADeprecationWarning
  filterwarnings('ignore', 'Using String type with no length for CREATE TABLE',
                 SADeprecationWarning)

  # Import Elixir & SQLAlchemy
  import elixir as _elixir
  from elixir import *
  from sqlalchemy import func
  import sqlalchemy as sql

  # Disable autosetup by recommendation from Jason R. Coombs:
  # http://groups.google.com/group/sqlelixir/msg/ed698d986bfeefdb
  options_defaults['autosetup'] = False

  # Control wheretere to include module name or not in table names.
  # If True, project.fruits.Apple -> table apples.
  # If False, project.fruits.Apple -> table project_fruits_apples.
  options_defaults['shortnames'] = True
  
  # Metadata configuration bind filter
  from smisk.config import config
  import logging
  log = logging.getLogger(__name__)
  def smisk_mvc_metadata(conf):
    dburi = conf.get('smisk.mvc.model.bind')
    if dburi is not None:
      log.info('binding to %r', dburi)
      metadata.bind = dburi
  config.add_filter(smisk_mvc_metadata)
  # dont export these
  del log
  del smisk_mvc_metadata
  del config
  
except ImportError:
  warn('Elixir and/or SQLAlchemy is not installed -- smisk.mvc.model is not available')
