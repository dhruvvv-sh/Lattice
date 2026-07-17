from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def ensure_runtime_schema():
    """
    Keep older local databases compatible with the current metadata model.

    SQLAlchemy create_all() creates missing tables, but it does not add columns
    to tables that already exist. This project does not have Alembic migrations
    yet, so we patch the small set of metadata columns added for sharded nodes.
    """

    inspector = inspect(engine)

    if "object_shards" not in inspector.get_table_names():
        return

    existing_columns = {
        column["name"]
        for column in inspector.get_columns("object_shards")
    }
    required_columns = {
        "node_id": "VARCHAR",
        "disk_id": "VARCHAR",
        "shard_size": "INTEGER",
        "shard_checksum": "VARCHAR",
        "copy_index": "INTEGER NOT NULL DEFAULT 0",
        "role": "VARCHAR NOT NULL DEFAULT 'primary'",
        "healthy": "BOOLEAN NOT NULL DEFAULT TRUE",
        "last_verified_at": "TIMESTAMP",
    }
    missing_columns = {
        name: column_type
        for name, column_type in required_columns.items()
        if name not in existing_columns
    }

    if not missing_columns:
        return

    with engine.begin() as connection:
        for name, column_type in missing_columns.items():
            if engine.dialect.name == "postgresql":
                connection.execute(
                    text(
                        f"ALTER TABLE object_shards "
                        f"ADD COLUMN IF NOT EXISTS {name} {column_type}"
                    )
                )
            else:
                connection.execute(
                    text(f"ALTER TABLE object_shards ADD COLUMN {name} {column_type}")
                )
