import asyncio
import os
import sysconfig
from logging.config import fileConfig

from sqlalchemy.engine import Connection

from alembic import context
from alembic.script import write_hooks
from app.database.session import Base, async_engine
from app.modules.calendar.models import *  # noqa: F403
from app.modules.chats.models import *  # noqa: F403
from app.modules.invites.models import *  # noqa: F403
from app.modules.logs.models import *  # noqa: F403
from app.modules.notifications.models import *  # noqa: F403
from app.modules.roles.models import *  # noqa: F403
from app.modules.tasks.models import *  # noqa: F403
from app.modules.user_sessions.models import *  # noqa: F403
from app.modules.users.models import *  # noqa: F403

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)  # type: ignore

target_metadata = Base.metadata


@write_hooks.register("ruff")
def run_ruff(filename, options):
    ruff = os.path.join(sysconfig.get_path("scripts"), "ruff")
    os.system(f"{ruff} {options['options']} {filename}")  # noqa: S605


# filter that ignores deleteon of this tables
# op.drop_table("user_note_m2m")
# op.drop_table("document_folder_m2m")
# op.drop_table("logs_to_session")
# op.drop_table("group_permission")
# op.drop_table("group_room_m2m")
# op.drop_table("document_permission_m2m")
# op.drop_table("room_folder_m2m")
# op.drop_table("permissions_to_urls_m2m_role")
# op.drop_table("permissions_to_urls")
# op.drop_table("document_note_m2m")
# op.drop_table("user_group")
# op.drop_table("group_roles_m2m")
# op.drop_table("user_room")


def include_object(object, name, type_, reflected, compare_to):  # noqa: A002, ARG001
    if type_ != "table":
        return True
    return name not in (
        "user_note_m2m",
        "document_folder_m2m",
        "logs_to_session",
        "group_permission",
        "group_room_m2m",
        "document_permission_m2m",
        "room_folder_m2m",
        "permissions_to_urls_m2m_role",
        "permissions_to_urls",
        "document_note_m2m",
        "user_group",
        "group_roles_m2m",
        "user_room",
    )


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = async_engine.url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = async_engine

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
