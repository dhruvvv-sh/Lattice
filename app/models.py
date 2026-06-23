from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Boolean
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Bucket(Base):
    __tablename__ = "buckets"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(
        String,
        unique=True,
        index=True,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


class Object(Base):
    __tablename__ = "objects"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    bucket_id = Column(
        Integer,
        ForeignKey("buckets.id"),
        nullable=False
    )

    object_name = Column(
        String,
        nullable=False
    )

    file_path = Column(
        String,
        nullable=False
    )

    checksum = Column(
        String,
        nullable=False
    )

    disk_name = Column(
        String,
        nullable=False
    )

    size = Column(
        Integer,
        nullable=False
    )

    content_type = Column(String)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    shards = relationship(
        "ObjectShard",
        back_populates="object",
        cascade="all, delete-orphan"
    )


class ObjectShard(Base):
    __tablename__ = "object_shards"

    id = Column(
        Integer,
        primary_key=True
    )

    object_id = Column(
        Integer,
        ForeignKey("objects.id"),
        nullable=False
    )

    shard_index = Column(
        Integer,
        nullable=False
    )

    disk_name = Column(
        String,
        nullable=False
    )

    shard_path = Column(
        String,
        nullable=False
    )

    is_parity = Column(
        Boolean,
        nullable=False
    )

    shard_size = Column(
        Integer,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    object = relationship(
        "Object",
        back_populates="shards"
    )