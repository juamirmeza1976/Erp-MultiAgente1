from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# --- BEGIN Manually added section to configure DB URL and metadata ---
import os
import sys
# Add the parent directory of this 'alembic' script directory to sys.path.
# The alembic script directory is erp_system/services/inventario_service/alembic.
# So, os.path.dirname(__file__) is .../alembic
# os.path.join(os.path.dirname(__file__), '..') is .../inventario_service
# This allows us to import modules like 'models' and 'database' from 'inventario_service'.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import Base as TargetModelBase  # Import Base from models.py
from database import settings as app_settings # Import settings from database.py

# Set the SQLAlchemy URL directly on the config object
# This overrides or provides the URL if alembic.ini is missing or not configured
if app_settings.DATABASE_URL:
    config.set_main_option('sqlalchemy.url', app_settings.DATABASE_URL)
# --- END Manually added section ---

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    # Check if the config file actually exists before trying to load it
    # This is to prevent errors if alembic.ini is truly missing
    if os.path.exists(config.config_file_name):
        fileConfig(config.config_file_name)
    else:
        print(f"Warning: Alembic config file {config.config_file_name} not found. Logging may not be configured.")


# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# target_metadata = None # Original line
target_metadata = TargetModelBase.metadata # Use the imported Base

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
