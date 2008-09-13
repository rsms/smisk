# encoding: utf-8

# Ignore the SA string type depr warning
from sqlalchemy.exceptions import SADeprecationWarning
from warnings import filterwarnings
filterwarnings('ignore', 'Using String type with no length for CREATE TABLE', SADeprecationWarning)

# Import Elixir
from elixir import *
