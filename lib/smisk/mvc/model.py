# encoding: utf-8
'''Model in MVC
'''
from warnings import filterwarnings, warn
import logging

log = logging.getLogger(__name__)

default_engine_opts = {}

try:
  # Ignore the SA string type depr warning
  from sqlalchemy.exceptions import SADeprecationWarning
  filterwarnings('ignore', 'Using String type with no length for CREATE TABLE',
                 SADeprecationWarning)
  
  # Import Elixir & SQLAlchemy
  from sqlalchemy import func
  import elixir, sqlalchemy as sql
  from sqlalchemy.pool import StaticPool
  import sqlalchemy.orm
  
  # Replace Elixir default session (evens out difference between Elixir 0.5 - 0.6)
  elixir.session = sqlalchemy.orm.scoped_session(sqlalchemy.orm.sessionmaker(
    autoflush=True, transactional=True))
  
  # Import Elixir
  from elixir import *
  
  # Disable autosetup since we call setup_all() in mvc.Application.setup()
  options_defaults['autosetup'] = False
  
  # Includes module name in table names if False.
  # If True, project.fruits.Apple -> table apple.
  # If False, project.fruits.Apple -> table project_fruits_apple.
  options_defaults['shortnames'] = True
  
  # Extended entity class
  def Entity_field_names(cls):
    for col in cls.c:
      yield col.key
  Entity.field_names = classmethod(Entity_field_names)
  
  def Entity__iter__(self):
    return self.to_dict().iteritems()
  Entity.__iter__ = Entity__iter__
  
  
  # Add Entity.to_dict for old Elixir versions
  __ev = elixir.__version__.split('.')
  if __ev[0] == '0' and int(__ev[1]) < 6:
    def Entity_to_dict(self, deep={}, exclude=[]):
      """Generate a JSON-style nested dict/list structure from an object."""
      col_prop_names = [p.key for p in self.c]
      data = dict([(name, getattr(self, name))
                   for name in col_prop_names if name not in exclude])
      for rname, rdeep in deep.iteritems():
        # This code is borrowed from Elixir 0.7 and fairly untested with <=0.5
        dbdata = getattr(self, rname)
        #FIXME: use attribute names (ie coltoprop) instead of column names
        fks = self.mapper.get_property(rname).remote_side
        exclude = [c.name for c in fks]
        if isinstance(dbdata, list):
          data[rname] = [o.to_dict(rdeep, exclude) for o in dbdata]
        else:
          data[rname] = dbdata.to_dict(rdeep, exclude)
      return data
    Entity.to_dict = Entity_to_dict
  del __ev
  
  
  # A static pool, since Smisk is not multi-threaded
  class SingleProcessPool(StaticPool):
    def __init__(self, *va, **kw):
      StaticPool.__init__(self, *va, **kw)
      self._init_va = va
      self._init_kw = kw
      logger_name = '%s.%s' % (self.__class__.__module__, self.__class__.__name__)
      self.logger = logging.getLogger(logger_name)
      if self.echo == 'debug':
        self.logger.setLevel(logging.DEBUG)
      elif self.echo is True:
        self.logger.setLevel(logging.INFO)
      elif self.echo is False:
        self.logger.setLevel(logging.NOTSET)
    
    def recreate(self):
      self.log("recreating")
      o = self.__class__(*self._init_va, **self._init_kw)
      o.logger = self.logger
      return o
    
  
  # MySQL-specific pool, handling dropped connections.
  # We derive from the StaticPool, only using one connection per process.
  class MySQLConnectionPool(SingleProcessPool):
    def do_get(self):
      # This works with MySQL-python >=1.2.2 and sets reconnect in the MySQL client
      # library for the current connection, and automatically reconnects if needed.
      self._conn.ping(True)
      return self.connection
    
  
  # Metadata configuration bind filter
  from smisk.config import config
  def smisk_mvc_metadata(conf):
    '''This config filter configures the underlying Elixir 
    and SQLAlchemy modules.
    '''
    global log
    conf = conf.get('smisk.mvc.model')
    if not conf:
      return
    
    # Aquire required parameter "url"
    try:
      url = conf['url']
    except KeyError:
      log.warn('missing required "url" parameter in "smisk.mvc.model" config')
      return
    
    # Parse url into an accessible structure
    from smisk.core import URL
    url_st = URL(url)
    
    # Make a copy of the default options
    engine_opts = default_engine_opts.copy()
    
    # MySQL
    if url_st.scheme.lower() == 'mysql':
      if 'poolclass' not in conf:
        conf['poolclass'] = MySQLConnectionPool
        log.debug('MySQL: setting poolclass=%r', conf['poolclass'])
        if 'pool_size' in conf:
          log.debug('MySQL: disabling pool_size')
          del conf['pool_size']
        if 'pool_size' in engine_opts:
          del engine_opts['pool_size']
      elif 'pool_recycle' not in conf and 'pool_recycle' not in engine_opts:
        # In case of user-configured custom pool_class
        conf['pool_recycle'] = 3600
        log.debug('MySQL: setting pool_recycle=%r', conf['pool_recycle'])
    elif 'poolclass' not in conf:
      # Others than MySQL should also use a kind of static pool
      conf['poolclass'] = SingleProcessPool
    
    # Demux configuration
    elixir_opts = {}
    for k,v in conf.iteritems():
      if k.startswith('elixir.'):
        elixir_opts[k[7:]] = v
      elif k != 'url':
        engine_opts[k] = v
    
    # Apply Elixir default options
    if elixir_opts:
      log.info('applying Elixir default options %r', elixir_opts)
      # We apply by iteration since options_defaults is not 
      # guaranteed to be a real dict.
      for k,v in elixir_opts.iteritems():
        options_defaults[k] = v
    
    # Mask out password, since we're logging this
    if url_st.password:
      url_st.password = '***'
    
    # Log configuration
    if engine_opts:
      log.info('binding to %r with options %r', str(url_st), engine_opts)
    else:
      log.info('binding to %r', str(url_st))
    
    # Dispose any previous connection
    if metadata.bind and hasattr(metadata.bind, 'dispose'):
      log.debug('disposing old connection %r', metadata.bind)
      metadata.bind.dispose()
    
    # Create, configure and bind engine
    metadata.bind = sql.create_engine(url, **engine_opts)
  
  config.add_filter(smisk_mvc_metadata)
  # dont export these
  del smisk_mvc_metadata
  del config
  
except ImportError, e:
  warn('Elixir and/or SQLAlchemy is not installed -- smisk.mvc.model is not '\
       'available. (%s)', e.message)
  
  # So mvc.Application can do "if model.metadata.bind: ..."
  class metadata(object):
    bind = None
  
  session = None


def commit_if_needed():
  mreg = session.registry()
  if mreg and mreg.transaction:
    if mreg.transaction.session and mreg.transaction._active:
      log.info('committing %r', mreg.transaction)
      mreg.transaction.commit()
    log.debug('removing transaction from %r', mreg)
    mreg.transaction = None

def rollback_if_needed():
  mreg = session.registry()
  if mreg and mreg.transaction:
    if mreg.transaction.session and mreg.transaction._active:
      log.info('rolling back %r', mreg.transaction)
      mreg.transaction.rollback()
    log.debug('removing transaction from %r', mreg)
    mreg.transaction = None
