from alembic import context

from app import models_registry  # noqa: F401
from app.core.config import get_settings
from app.core.database import Base, get_engine

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(url=get_settings().database_url, target_metadata=target_metadata, literal_binds=True,
                      render_as_batch=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    with get_engine().connect() as conn:
        # SQLite admite DDL transaccional: una migración se aplica completa o no se aplica
        context.configure(connection=conn, target_metadata=target_metadata, render_as_batch=True,
                          transactional_ddl=True, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
