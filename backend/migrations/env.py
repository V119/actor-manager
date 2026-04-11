import logging
from logging.config import fileConfig
from alembic import context
from infrastructure.orm_models import database, ActorModel, PortraitModel, StyleModel, GeneratedResultModel, ProtocolModel

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's Meta.target_metadata here
# for 'autogenerate' support
# target_metadata = None
# For Peewee, we don't have metadata like SQLAlchemy

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=None,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # We use Peewee's connection if possible, or just the URL
    connectable = database

    # Since Peewee isn't SQLAlchemy, we handle connection differently if needed
    # but Alembic expects a SQLAlchemy engine for 'online' mode by default.
    # However, we can just use the DB URL from config.

    from sqlalchemy import create_engine
    url = config.get_main_option("sqlalchemy.url")
    engine = create_engine(url)

    with engine.connect() as connection:
        context.configure(
            connection=connection, target_metadata=None
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
