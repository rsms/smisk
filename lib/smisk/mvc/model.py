# encoding: utf-8

# Ignore the SA string type depr warning
from sqlalchemy.exceptions import SADeprecationWarning
from warnings import filterwarnings
filterwarnings('ignore', 'Using String type with no length for CREATE TABLE',
               SADeprecationWarning)

# Import Elixir
from elixir import *

# Disable autosetup by recommendation from Jason R. Coombs:
# http://groups.google.com/group/sqlelixir/msg/ed698d986bfeefdb
options_defaults['autosetup'] = False
