from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


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
        default=utc_now
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
        default=utc_now
    )

    shards = relationship(
        "ObjectShard",
        back_populates="object",
        cascade="all, delete-orphan"
    )

    placement_manifest = relationship(
        "ObjectPlacementManifest",
        back_populates="object",
        cascade="all, delete-orphan",
        uselist=False
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

    node_id = Column(
        String,
        nullable=True
    )

    disk_id = Column(
        String,
        nullable=True
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

    shard_checksum = Column(
        String,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=utc_now
    )

    object = relationship(
        "Object",
        back_populates="shards"
    )


class ObjectPlacementManifest(Base):
    __tablename__ = "object_placement_manifests"

    id = Column(
        Integer,
        primary_key=True
    )

    object_id = Column(
        Integer,
        ForeignKey("objects.id"),
        unique=True,
        nullable=False
    )

    strategy = Column(
        String,
        nullable=False
    )

    manifest = Column(
        JSON,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=utc_now
    )

    object = relationship(
        "Object",
        back_populates="placement_manifest"
    )
