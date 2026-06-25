import os
from logging.config import fileConfig
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from alembic import context

env_path = Path(__file__).parents[1] / ".env"
load_dotenv(env_path)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# grab variables
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
name = os.getenv("DB_NAME")

if not all([user, password, host, port, name]):
    raise RuntimeError("One or more DB_* env vars are missing")

DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{name}"


if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL must be set")

config.set_main_option("sqlalchemy.url", DATABASE_URL)

fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from dashboard.src.db import Base

# Import all models so Base.metadata is fully populated for autogenerate
import dashboard.src.ai.models.voice_query  # noqa: F401
import dashboard.src.calendars.models.calendar_event  # noqa: F401
import dashboard.src.calendars.models.todo  # noqa: F401
import dashboard.src.data.models.device_event  # noqa: F401
import dashboard.src.learning.models.card  # noqa: F401
import dashboard.src.learning.models.checklist  # noqa: F401
import dashboard.src.learning.models.checklist_note  # noqa: F401
import dashboard.src.learning.models.problem  # noqa: F401
import dashboard.src.learning.models.quiz  # noqa: F401
import dashboard.src.learning.models.reminder  # noqa: F401
import dashboard.src.learning.models.routine_task  # noqa: F401
import dashboard.src.learning.models.score  # noqa: F401
import dashboard.src.learning.models.study  # noqa: F401
import dashboard.src.learning.models.subject  # noqa: F401
import dashboard.src.learning.models.topic  # noqa: F401

target_metadata = Base.metadata

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
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
