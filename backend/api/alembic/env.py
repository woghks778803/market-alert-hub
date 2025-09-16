import os, sys
from logging.config import fileConfig
from typing import Any, Dict
from sqlalchemy import engine_from_config, pool
from alembic import context

# ----- 모듈 경로 보정: /app 를 sys.path에 추가 -----
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.core import settings
from app.model.base import Base

# Alembic 기본 설정
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.SQLALCHEMY_URL)
target_metadata = Base.metadata

section_raw = config.get_section(config.config_ini_section)
if section_raw is None:  # type: ignore
    raise RuntimeError("Alembic config section not found")

section: Dict[str, Any] = dict(section_raw)


def run_migrations_offline():
    context.configure(
        url=settings.SQLALCHEMY_URL, target_metadata=target_metadata, literal_binds=True
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        section,
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
