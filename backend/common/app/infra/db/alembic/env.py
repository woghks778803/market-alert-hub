import os, sys
from urllib.parse import quote_plus
from logging.config import fileConfig
from typing import Any, Dict
from sqlalchemy import engine_from_config, pool
from alembic import context

# ----- 모듈 경로 보정: /app 를 sys.path에 추가 -----
# sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.infra.db.base import Base
import app.infra.db.model

# Alembic 기본 설정
required = [
    "MYSQL_USER",
    "MYSQL_PASSWORD",
    "MYSQL_HOST",
    "MYSQL_PORT",
    "MYSQL_DATABASE",
]
missing = [k for k in required if not os.environ.get(k)]
if missing:
    raise RuntimeError(f"Missing env for alembic DB url: {missing}")
SQLALCHEMY_URL = f"mysql+pymysql://{os.environ['MYSQL_USER']}:{quote_plus(os.environ['MYSQL_PASSWORD'])}@{os.environ['MYSQL_HOST']}:{os.environ['MYSQL_PORT']}/{os.environ['MYSQL_DATABASE']}?charset=utf8mb4"

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option(
    "sqlalchemy.url",
    SQLALCHEMY_URL,
)
# config.set_main_option("sqlalchemy.url", settings.SQLALCHEMY_URL)
target_metadata = Base.metadata

section_raw = config.get_section(config.config_ini_section)
if section_raw is None:  # type: ignore
    raise RuntimeError("Alembic config section not found")

section = dict(section_raw)


def run_migrations_offline():
    context.configure(
        url=SQLALCHEMY_URL, target_metadata=target_metadata, literal_binds=True
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
