from logging.config import fileConfig
import os
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
# add your model's MetaData object here for 'autogenerate' support
# for example: from myapp import mymodel
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.models.domain import db, Domain, Report
# the SQLAlchemy URL
DATABASE_URL = os.environ.get('DATABASE_URL') or os.environ.get('SQLALCHEMY_DATABASE_URI') or 'postgresql://key65drop:eY73j9Emr4MWNjbkTPPm@db:5432/dropanalyzer'
config.set_main_option('sqlalchemy.url', DATABASE_URL)
target_metadata = db.metadata
def run_migrations_offline():
    context.configure(url=DATABASE_URL, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
